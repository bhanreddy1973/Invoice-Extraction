from decimal import Decimal

from src.validation.financial_validator import validate_financials
from src.validation.invoice_schema import InvoiceExtraction


def test_financial_match():
    inv = InvoiceExtraction.model_validate(
        {
            "is_invoice": True,
            "vendor": "Acme",
            "invoice_number": "1",
            "invoice_date": "2026-03-14",
            "currency": "INR",
            "line_items": [{"description": "A4", "quantity": 10, "amount": 3200.0}],
            "tax_total": 576.0,
            "total": 3776.0,
        }
    )
    result = validate_financials(inv, tolerance=Decimal("0.05"))
    assert result.is_valid
    assert result.expected_total == Decimal("3776.0")


def test_financial_mismatch():
    inv = InvoiceExtraction.model_validate(
        {
            "is_invoice": True,
            "vendor": "Acme",
            "invoice_number": "1",
            "invoice_date": "2026-03-14",
            "currency": "INR",
            "line_items": [{"description": "A4", "quantity": 10, "amount": 3200.0}],
            "tax_total": 576.0,
            "total": 4000.0,
        }
    )
    result = validate_financials(inv)
    assert not result.is_valid
    assert result.reason == "financial_mismatch"


def test_negative_discount_line():
    inv = InvoiceExtraction.model_validate(
        {
            "is_invoice": True,
            "vendor": "Studio",
            "invoice_number": "PHS",
            "invoice_date": "2026-03-14",
            "currency": "USD",
            "line_items": [
                {"description": "Work", "quantity": 1, "amount": 1000.0},
                {"description": "Discount", "quantity": None, "amount": -100.0},
            ],
            "tax_total": 90.0,
            "total": 990.0,
        }
    )
    assert validate_financials(inv).is_valid
