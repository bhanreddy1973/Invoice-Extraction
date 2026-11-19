from decimal import Decimal

from src.evaluation.normalizer import normalize_currency, normalize_string, numbers_equal
from src.evaluation.evaluator import Evaluator
from src.pipeline import PipelineResult


def test_number_normalization():
    assert numbers_equal("1,200.00", 1200)
    assert numbers_equal(1200, 1200.00)


def test_vendor_normalization():
    assert normalize_string(" Acme   Pvt Ltd ") == normalize_string("acme pvt ltd")


def test_currency_normalization():
    assert normalize_currency("inr") == "INR"


def test_compare_non_invoice():
    evaluator = Evaluator(pipeline=None)  # type: ignore[arg-type]
    result = PipelineResult(
        document="L08.pdf",
        status="success",
        route="pdf_text",
        invoice={
            "is_invoice": False,
            "vendor": None,
            "invoice_number": None,
            "invoice_date": None,
            "currency": None,
            "line_items": None,
            "tax_total": None,
            "total": None,
        },
        schema_valid=True,
        financial={"is_valid": True},
        review={"needs_review": False},
    )
    gt = {
        "is_invoice": False,
        "vendor": None,
        "invoice_number": None,
        "invoice_date": None,
        "currency": None,
        "line_items": None,
        "tax_total": None,
        "total": None,
    }
    doc = evaluator._compare("L08.pdf", result, gt)
    assert doc.overall_exact
