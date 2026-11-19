"""Baseline financial consistency checks using Decimal arithmetic."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from src.validation.invoice_schema import InvoiceExtraction


@dataclass
class FinancialValidationResult:
    is_valid: bool
    expected_total: Decimal | None
    extracted_total: Decimal | None
    difference: Decimal | None
    reason: str
    ambiguous: bool = False


def _as_decimal(value: float | int | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def validate_financials(
    extraction: InvoiceExtraction,
    *,
    tolerance: Decimal = Decimal("0.05"),
) -> FinancialValidationResult:
    """Check sum(line amounts) + tax_total ≈ total for invoices."""
    if not extraction.is_invoice:
        return FinancialValidationResult(
            is_valid=True,
            expected_total=None,
            extracted_total=None,
            difference=None,
            reason="non_invoice_skipped",
        )

    if extraction.line_items is None or extraction.total is None:
        return FinancialValidationResult(
            is_valid=False,
            expected_total=None,
            extracted_total=_as_decimal(extraction.total),
            difference=None,
            reason="missing_line_items_or_total",
            ambiguous=True,
        )

    line_sum = sum((_as_decimal(item.amount) or Decimal("0") for item in extraction.line_items), Decimal("0"))
    tax = _as_decimal(extraction.tax_total)
    if tax is None:
        return FinancialValidationResult(
            is_valid=False,
            expected_total=None,
            extracted_total=_as_decimal(extraction.total),
            difference=None,
            reason="missing_tax_total",
            ambiguous=True,
        )

    expected = line_sum + tax
    extracted = _as_decimal(extraction.total)
    assert extracted is not None
    difference = (expected - extracted).copy_abs()

    if difference <= tolerance:
        return FinancialValidationResult(
            is_valid=True,
            expected_total=expected,
            extracted_total=extracted,
            difference=difference,
            reason="totals_match",
        )

    # Ambiguous when discounts/fees may sit outside line items
    return FinancialValidationResult(
        is_valid=False,
        expected_total=expected,
        extracted_total=extracted,
        difference=difference,
        reason="financial_mismatch",
        ambiguous=True,
    )
