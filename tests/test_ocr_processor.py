from pathlib import Path

from src.config import get_settings
from src.document_processing.document_router import DocumentRouter

ROOT = Path(__file__).resolve().parents[1]
L02 = ROOT / "data" / "raw" / "labelled" / "L02.jpg"
L09 = ROOT / "data" / "raw" / "labelled" / "L09.pdf"


def test_image_routes_to_ocr_or_vision():
    routed = DocumentRouter(get_settings()).route(L02)
    assert routed.route in {"ocr", "vision"}
    assert routed.images_png


def test_scanned_pdf_not_pdf_text():
    routed = DocumentRouter(get_settings()).route(L09)
    assert routed.route in {"ocr", "vision"}
