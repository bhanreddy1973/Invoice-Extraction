from dataclasses import replace
from pathlib import Path

from src.config import get_settings
from src.document_processing.document_router import DocumentRouter

ROOT = Path(__file__).resolve().parents[1]
L01 = ROOT / "data" / "raw" / "labelled" / "L01.pdf"
L02 = ROOT / "data" / "raw" / "labelled" / "L02.jpg"
L09 = ROOT / "data" / "raw" / "labelled" / "L09.pdf"


def test_vision_mode_forces_image_to_vision():
    settings = replace(get_settings(), extraction_mode="vision")
    routed = DocumentRouter(settings).route(L02)
    assert routed.route == "vision"
    assert routed.images_png
    assert "ocr_disabled" in routed.notes


def test_vision_mode_forces_scanned_pdf_to_vision():
    settings = replace(get_settings(), extraction_mode="vision")
    routed = DocumentRouter(settings).route(L09)
    assert routed.route == "vision"
    assert routed.images_png


def test_vision_mode_forces_digital_pdf_to_vision():
    settings = replace(get_settings(), extraction_mode="vision")
    routed = DocumentRouter(settings).route(L01)
    assert routed.route == "vision"
    assert routed.images_png


def test_hybrid_image_routes_to_ocr_or_vision():
    settings = replace(get_settings(), extraction_mode="hybrid")
    routed = DocumentRouter(settings).route(L02)
    assert routed.route in {"ocr", "vision"}
    assert routed.images_png
