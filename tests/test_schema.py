from src.validation.invoice_schema import InvoiceExtraction, non_invoice_result
from src.validation.schema_validator import validate_extraction_payload
from src.exceptions import SchemaValidationFailedError
import pytest


def test_valid_invoice_schema():
    payload = {
        "is_invoice": True,
        "vendor": "Acme",
        "invoice_number": "INV-1",
        "invoice_date": "2026-03-14",
        "currency": "inr",
        "line_items": [{"description": "Paper", "quantity": 10, "amount": 100.0}],
        "tax_total": 18.0,
        "total": 118.0,
    }
    model = validate_extraction_payload(payload)
    assert model.currency == "INR"


def test_non_invoice_nulls():
    model = non_invoice_result()
    assert model.is_invoice is False
    assert model.vendor is None


def test_rejects_non_invoice_with_vendor():
    with pytest.raises(SchemaValidationFailedError):
        validate_extraction_payload(
            {
                "is_invoice": False,
                "vendor": "Nope",
                "invoice_number": None,
                "invoice_date": None,
                "currency": None,
                "line_items": None,
                "tax_total": None,
                "total": None,
            }
        )


def test_nullable_quantity_allowed():
    model = InvoiceExtraction.model_validate(
        {
            "is_invoice": True,
            "vendor": "A",
            "invoice_number": "1",
            "invoice_date": "2026-01-01",
            "currency": "USD",
            "line_items": [{"description": "Retainer", "quantity": None, "amount": 100.0}],
            "tax_total": 0,
            "total": 100.0,
        }
    )
    assert model.line_items[0].quantity is None
