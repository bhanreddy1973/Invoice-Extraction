from decimal import Decimal

from src.extraction.escalate import should_escalate_to_vision
from src.validation.financial_validator import FinancialValidationResult
from src.validation.invoice_schema import InvoiceExtraction


def _invoice(**kwargs):
    base = {
        "is_invoice": True,
        "vendor": "Acme",
        "invoice_number": "1",
        "invoice_date": "2026-01-01",
        "currency": "INR",
        "line_items": [{"description": "A", "quantity": 1, "amount": 10.0}],
        "tax_total": 1.0,
        "total": 11.0,
    }
    base.update(kwargs)
    return InvoiceExtraction.model_validate(base)


def _ok_financial():
    return FinancialValidationResult(
        is_valid=True,
        expected_total=Decimal("11"),
        extracted_total=Decimal("11"),
        difference=Decimal("0"),
        reason="totals_match",
    )


def test_escalate_on_missing_vendor():
    inv = _invoice(vendor=None)
    # schema forbids vendor None with is_invoice true? Actually vendor can be null in schema.
    ok, reason = should_escalate_to_vision(inv, _ok_financial(), route="pdf_text", has_images=True)
    assert ok
    assert "vendor" in reason


def test_escalate_ocr_null_quantities():
    inv = _invoice(
        line_items=[
            {"description": "A", "quantity": None, "amount": 10.0},
            {"description": "B", "quantity": None, "amount": 20.0},
        ]
    )
    ok, reason = should_escalate_to_vision(inv, _ok_financial(), route="ocr", has_images=True)
    assert ok
    assert reason == "ocr_null_quantities"


def test_no_escalate_pdf_text_null_quantities():
    inv = _invoice(
        line_items=[
            {"description": "Retainer", "quantity": None, "amount": 100.0},
        ]
    )
    ok, _ = should_escalate_to_vision(inv, _ok_financial(), route="pdf_text", has_images=True)
    assert not ok


def test_ocr_route_always_confirms_with_vision():
    inv = _invoice()
    ok, reason = should_escalate_to_vision(inv, _ok_financial(), route="ocr", has_images=True)
    assert ok
    assert reason == "ocr_confirm_vision"


def test_no_escalate_without_images():
    inv = _invoice(vendor=None)
    ok, _ = should_escalate_to_vision(inv, _ok_financial(), route="ocr", has_images=False)
    assert not ok
