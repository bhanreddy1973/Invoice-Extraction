"""End-to-end invoice extraction pipeline."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings
from src.document_processing.document_router import DocumentRouter, RoutedDocument
from src.document_processing.image_processor import ImageProcessor
from src.document_processing.pdf_processor import PDFProcessor
from src.exceptions import FinancialValidationFailedError, InvoicePipelineError
from src.extraction.escalate import should_escalate_to_vision
from src.extraction.extractor import ExtractionResult, Extractor
from src.llm.base import BaseLLMProvider
from src.monitoring.cost_tracker import CostTracker
from src.monitoring.usage_tracker import UsageTracker
from src.validation.financial_validator import FinancialValidationResult, validate_financials
from src.validation.invoice_schema import InvoiceExtraction

logger = logging.getLogger(__name__)


def _jsonable(value: Any) -> Any:
    """Convert Decimals and nested structures into JSON-safe values."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


@dataclass
class ReviewMetadata:
    needs_review: bool
    review_reason: str | None = None
    confidence_score: float | None = None


@dataclass
class PipelineResult:
    document: str
    status: str  # success | error
    route: str | None
    invoice: dict[str, Any] | None
    schema_valid: bool
    financial: dict[str, Any] | None
    review: dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None
    latency_seconds: float = 0.0
    cost: dict[str, Any] | None = None
    model_used: str | None = None
    notes: list[str] = field(default_factory=list)

    def public_invoice_json(self) -> dict[str, Any] | None:
        return self.invoice


class InvoicePipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.usage_tracker = UsageTracker()
        self.cost_tracker = CostTracker()
        self.router = DocumentRouter(self.settings)
        self.extractor = Extractor(provider=provider, settings=self.settings, usage_tracker=self.usage_tracker)
        self.pdf = PDFProcessor(alnum_threshold=self.settings.pdf_text_alnum_threshold)
        self.images = ImageProcessor()

    def process(self, path: Path | str) -> PipelineResult:
        path = Path(path)
        started = time.perf_counter()
        routed: RoutedDocument | None = None
        notes: list[str] = []
        try:
            routed = self.router.route(path)
            notes = list(routed.notes)

            extraction = self.extractor.extract(routed)
            financial = validate_financials(
                extraction.invoice,
                tolerance=self.settings.financial_tolerance,
            )

            # OCR/text first pass → vision repair when needed
            if not self.settings.disable_ocr:
                self._ensure_images(routed)
                escalate, reason = should_escalate_to_vision(
                    extraction.invoice,
                    financial,
                    route=routed.route,
                    has_images=bool(routed.images_png),
                )
                if escalate:
                    logger.info(
                        "Escalating %s to vision (%s); first model=%s",
                        path.name,
                        reason,
                        extraction.model_used,
                    )
                    notes.append(f"vision_escalate={reason}")
                    vision_result = self.extractor.extract(routed, force_vision=True)
                    vision_result.usages = extraction.usages + vision_result.usages
                    vision_result.attempts = extraction.attempts + vision_result.attempts
                    vision_result.escalated_to_vision = True
                    vision_result.escalate_reason = reason
                    extraction = vision_result
                    financial = validate_financials(
                        extraction.invoice,
                        tolerance=self.settings.financial_tolerance,
                    )
                    routed.route = f"{routed.route}->vision"
                    notes.append(f"final_model={extraction.model_used}")

            review = self._review_decision(extraction.invoice, financial, routed)
            cost = self.cost_tracker.estimate_many(extraction.usages)

            if (
                extraction.invoice.is_invoice
                and not financial.is_valid
                and not financial.ambiguous
            ):
                raise FinancialValidationFailedError(financial.reason)

            return PipelineResult(
                document=path.name,
                status="success",
                route=routed.route,
                invoice=extraction.invoice.to_public_dict(),
                schema_valid=True,
                financial=_jsonable(asdict(financial)),
                review=asdict(review),
                latency_seconds=time.perf_counter() - started,
                cost=asdict(cost),
                model_used=extraction.model_used,
                notes=notes,
            )
        except InvoicePipelineError as exc:
            logger.error("Pipeline error for %s: %s", path.name, exc)
            return PipelineResult(
                document=path.name,
                status="error",
                route=routed.route if routed else None,
                invoice=None,
                schema_valid=False,
                financial=None,
                review=asdict(ReviewMetadata(needs_review=True, review_reason=exc.code)),
                error_code=exc.code,
                error_message=exc.message,
                latency_seconds=time.perf_counter() - started,
                notes=notes or (list(routed.notes) if routed else []),
            )

    def _ensure_images(self, routed: RoutedDocument) -> None:
        """Lazy-render images so vision escalate can run after a text/OCR pass."""
        if routed.images_png:
            return
        suffix = routed.path.suffix.lower()
        try:
            if suffix == ".pdf":
                routed.images_png = self.pdf.render_pages(routed.path)
            elif suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
                image = self.images.load(routed.path)
                routed.images_png = [self.images.to_png_bytes(image)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not prepare images for escalate on %s: %s", routed.path.name, exc)

    def process_and_save(self, path: Path | str, output_path: Path | str | None = None) -> PipelineResult:
        result = self.process(path)
        if output_path and result.invoice is not None:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result.invoice, indent=2), encoding="utf-8")
        return result

    def _review_decision(
        self,
        invoice: InvoiceExtraction,
        financial: FinancialValidationResult,
        routed: RoutedDocument,
    ) -> ReviewMetadata:
        if invoice.is_invoice and not financial.is_valid:
            return ReviewMetadata(
                needs_review=True,
                review_reason=financial.reason,
                confidence_score=None,
            )
        if (
            not self.settings.disable_ocr
            and "vision" in (routed.route or "")
            and routed.ocr_alnum < self.settings.pdf_text_alnum_threshold
            and routed.ocr_alnum > 0
        ):
            return ReviewMetadata(
                needs_review=True,
                review_reason="low_ocr_quality_vision_route",
                confidence_score=None,
            )
        if invoice.is_invoice and (
            not invoice.vendor or not invoice.invoice_number or invoice.total is None
        ):
            return ReviewMetadata(
                needs_review=True,
                review_reason="missing_critical_fields",
                confidence_score=None,
            )
        return ReviewMetadata(needs_review=False, review_reason=None, confidence_score=None)
