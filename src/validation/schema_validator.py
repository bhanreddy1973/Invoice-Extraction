"""Validate raw LLM payloads against the InvoiceExtraction schema."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.exceptions import SchemaValidationFailedError
from src.validation.invoice_schema import InvoiceExtraction


def validate_extraction_payload(payload: dict[str, Any]) -> InvoiceExtraction:
    try:
        return InvoiceExtraction.model_validate(payload)
    except ValidationError as exc:
        raise SchemaValidationFailedError(str(exc)) from exc
