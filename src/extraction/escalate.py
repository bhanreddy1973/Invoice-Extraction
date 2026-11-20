"""Decide when a first-pass extraction should escalate to vision."""

from __future__ import annotations

from src.validation.financial_validator import FinancialValidationResult
from src.validation.invoice_schema import InvoiceExtraction


def missing_critical_fields(invoice: InvoiceExtraction) -> list[str]:
    """Return names of critical invoice fields that are missing."""
    if not invoice.is_invoice:
        return []
    missing: list[str] = []
    if not invoice.vendor:
        missing.append("vendor")
    if not invoice.invoice_number:
        missing.append("invoice_number")
    if not invoice.invoice_date:
        missing.append("invoice_date")
    if not invoice.currency:
        missing.append("currency")
    if invoice.tax_total is None:
        missing.append("tax_total")
    if invoice.total is None:
        missing.append("total")
    if not invoice.line_items:
        missing.append("line_items")
    return missing


def suspicious_ocr_line_items(invoice: InvoiceExtraction, *, route: str) -> bool:
    """OCR often drops quantities; escalate when qty is null on an OCR first pass."""
    if route != "ocr" or not invoice.is_invoice or not invoice.line_items:
        return False
    null_qty = sum(1 for item in invoice.line_items if item.quantity is None)
    return null_qty >= max(1, len(invoice.line_items) // 2)


def should_escalate_to_vision(
    invoice: InvoiceExtraction,
    financial: FinancialValidationResult,
    *,
    route: str,
    has_images: bool,
) -> tuple[bool, str]:
    """
    Escalate text/OCR first-pass results to vision when repair is likely needed.

    Digital pdf_text passes escalate only on missing fields / financial failure.
    OCR passes also escalate when many line-item quantities are null.
    """
    if not has_images:
        return False, ""
    if route == "vision":
        return False, ""

    missing = missing_critical_fields(invoice)
    if missing:
        return True, "missing_fields:" + ",".join(missing)

    if invoice.is_invoice and not financial.is_valid:
        return True, f"financial:{financial.reason}"

    if suspicious_ocr_line_items(invoice, route=route):
        return True, "ocr_null_quantities"

    # OCR text is often "complete" but wrong (bad digits/qty). Always confirm scans/photos with vision.
    if route == "ocr":
        return True, "ocr_confirm_vision"

    return False, ""
