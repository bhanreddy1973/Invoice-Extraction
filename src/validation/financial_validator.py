"""Financial consistency checks using Decimal arithmetic + qty×unit_price priority."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from src.validation.invoice_schema import InvoiceExtraction

TWOPLACES = Decimal("0.01")


@dataclass
class FinancialValidationResult:
    is_valid: bool
    expected_total: Decimal | None
    extracted_total: Decimal | None
    difference: Decimal | None
    reason: str
    ambiguous: bool = False
    amount_corrections: int = 0


def _as_decimal(value: float | int | str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def apply_unit_price_priority(
    extraction: InvoiceExtraction,
    *,
    tolerance: Decimal = Decimal("0.05"),
) -> int:
    """Prefer amount = quantity × unit_price when both are present (mutates in place).

    Returns the number of line amounts overwritten.
    """
    if not extraction.is_invoice or not extraction.line_items:
        return 0

    corrections = 0
    for item in extraction.line_items:
        if item.quantity is None or item.unit_price is None:
            continue
        qty = _as_decimal(item.quantity)
        rate = _as_decimal(item.unit_price)
        if qty is None or rate is None:
            continue
        computed = (qty * rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        old = _as_decimal(item.amount)
        item.amount = float(computed)
        if old is None or (old - computed).copy_abs() > tolerance:
            corrections += 1
    return corrections


def validate_financials(
    extraction: InvoiceExtraction,
    *,
    tolerance: Decimal = Decimal("0.05"),
) -> FinancialValidationResult:
    """Apply qty×unit_price priority, then check sum(line amounts) + tax_total ≈ total."""
    if not extraction.is_invoice:
        return FinancialValidationResult(
            is_valid=True,
            expected_total=None,
            extracted_total=None,
            difference=None,
            reason="non_invoice_skipped",
        )

    corrections = apply_unit_price_priority(extraction, tolerance=tolerance)

    if extraction.line_items is None or extraction.total is None:
        return FinancialValidationResult(
            is_valid=False,
            expected_total=None,
            extracted_total=_as_decimal(extraction.total),
            difference=None,
            reason="missing_line_items_or_total",
            ambiguous=True,
            amount_corrections=corrections,
        )

    line_sum = sum(
        (_as_decimal(item.amount) or Decimal("0") for item in extraction.line_items),
        Decimal("0"),
    )
    tax = _as_decimal(extraction.tax_total)
    if tax is None:
        return FinancialValidationResult(
            is_valid=False,
            expected_total=None,
            extracted_total=_as_decimal(extraction.total),
            difference=None,
            reason="missing_tax_total",
            ambiguous=True,
            amount_corrections=corrections,
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
            amount_corrections=corrections,
        )

    # Ambiguous when discounts/fees may sit outside line items
    return FinancialValidationResult(
        is_valid=False,
        expected_total=expected,
        extracted_total=extracted,
        difference=difference,
        reason="financial_mismatch",
        ambiguous=True,
        amount_corrections=corrections,
    )
