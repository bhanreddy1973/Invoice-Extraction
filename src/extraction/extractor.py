"""High-level extraction service with retries and optional vision escalate."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.config import Settings, get_settings
from src.document_processing.document_router import RoutedDocument
from src.exceptions import (
    InvalidJSONError,
    SchemaValidationFailedError,
    UnreadableDocumentError,
)
from src.extraction.response_parser import extract_json_object
from src.llm.base import BaseLLMProvider, LLMResponse, LLMUsage
from src.llm.prompts import (
    RETRY_FEEDBACK_TEMPLATE,
    SYSTEM_PROMPT,
    USER_TEXT_TEMPLATE,
    USER_VISION_TEMPLATE,
)
from src.llm.provider import NVIDIAProvider
from src.monitoring.usage_tracker import UsageTracker
from src.validation.invoice_schema import InvoiceExtraction
from src.validation.schema_validator import validate_extraction_payload

logger = logging.getLogger(__name__)


@dataclass
class ExtractionAttempt:
    raw_text: str
    error: str | None = None
    mode: str = "text"  # text | vision


@dataclass
class ExtractionResult:
    invoice: InvoiceExtraction
    usages: list[LLMUsage] = field(default_factory=list)
    attempts: list[ExtractionAttempt] = field(default_factory=list)
    model_used: str | None = None
    escalated_to_vision: bool = False
    escalate_reason: str | None = None


class Extractor:
    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        settings: Settings | None = None,
        usage_tracker: UsageTracker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.provider = provider or NVIDIAProvider(self.settings)
        self.usage_tracker = usage_tracker or UsageTracker()

    def extract(self, routed: RoutedDocument, *, force_vision: bool = False) -> ExtractionResult:
        if routed.route == "unreadable":
            raise UnreadableDocumentError(f"Document marked unreadable: {routed.path.name}")

        use_vision = force_vision or routed.route == "vision" or (
            (not routed.text or sum(c.isalnum() for c in routed.text) < 20) and bool(routed.images_png)
        )

        if use_vision:
            if not routed.images_png:
                raise UnreadableDocumentError(f"Vision route has no images: {routed.path.name}")
            base_user = USER_VISION_TEMPLATE.format(ocr_hint=routed.text or "")
            mode = "vision"
        else:
            if not routed.text or sum(c.isalnum() for c in routed.text) < 20:
                raise UnreadableDocumentError(f"Insufficient text for extraction: {routed.path.name}")
            base_user = USER_TEXT_TEMPLATE.format(document_text=routed.text)
            mode = "text"

        attempts: list[ExtractionAttempt] = []
        usages: list[LLMUsage] = []
        feedback: str | None = None
        previous_json: str | None = None
        last_error: Exception | None = None

        for _ in range(self.settings.llm_max_retries + 1):
            user = base_user
            if feedback and previous_json:
                user = (
                    base_user
                    + "\n\n"
                    + RETRY_FEEDBACK_TEMPLATE.format(feedback=feedback, previous_json=previous_json)
                )

            response = self._invoke(use_vision=use_vision, user=user, images=routed.images_png)
            usages.append(response.usage)
            self.usage_tracker.record(response.usage)
            attempts.append(ExtractionAttempt(raw_text=response.content, mode=mode))

            try:
                payload = extract_json_object(response.content)
                invoice = validate_extraction_payload(payload)
                return ExtractionResult(
                    invoice=invoice,
                    usages=usages,
                    attempts=attempts,
                    model_used=response.model,
                    escalated_to_vision=force_vision,
                )
            except (InvalidJSONError, SchemaValidationFailedError) as exc:
                last_error = exc
                attempts[-1].error = str(exc)
                feedback = str(exc)
                previous_json = response.content
                logger.warning("Extraction validation failed for %s: %s", routed.path.name, exc)

        assert last_error is not None
        raise last_error

    def _invoke(self, *, use_vision: bool, user: str, images: list[bytes]) -> LLMResponse:
        if use_vision:
            return self.provider.complete_vision(system=SYSTEM_PROMPT, user=user, images_png=images)
        return self.provider.complete_text(system=SYSTEM_PROMPT, user=user)
