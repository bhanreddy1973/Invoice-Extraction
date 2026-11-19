"""Typed errors for the invoice extraction pipeline."""

from __future__ import annotations


class InvoicePipelineError(Exception):
    """Base error with a stable machine-readable code."""

    code: str = "PIPELINE_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message


class UnsupportedFormatError(InvoicePipelineError):
    code = "UNSUPPORTED_FORMAT"


class CorruptFileError(InvoicePipelineError):
    code = "CORRUPT_FILE"


class EmptyDocumentError(InvoicePipelineError):
    code = "EMPTY_DOCUMENT"


class UnreadableDocumentError(InvoicePipelineError):
    code = "UNREADABLE_DOCUMENT"


class LLMTimeoutError(InvoicePipelineError):
    code = "LLM_TIMEOUT"


class LLMRateLimitError(InvoicePipelineError):
    code = "LLM_RATE_LIMIT"


class LLMProviderError(InvoicePipelineError):
    code = "LLM_PROVIDER_ERROR"


class InvalidJSONError(InvoicePipelineError):
    code = "INVALID_JSON"


class SchemaValidationFailedError(InvoicePipelineError):
    code = "SCHEMA_VALIDATION_FAILED"


class FinancialValidationFailedError(InvoicePipelineError):
    code = "FINANCIAL_VALIDATION_FAILED"


class FileTooLargeError(InvoicePipelineError):
    code = "FILE_TOO_LARGE"
