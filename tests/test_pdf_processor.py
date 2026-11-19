from pathlib import Path

from src.document_processing.pdf_processor import PDFProcessor

ROOT = Path(__file__).resolve().parents[1]
L01 = ROOT / "data" / "raw" / "labelled" / "L01.pdf"
L09 = ROOT / "data" / "raw" / "labelled" / "L09.pdf"


def test_digital_pdf_has_text():
    info = PDFProcessor().open_info(L01)
    assert info.has_meaningful_text
    assert info.page_count == 1
    assert "INVOICE" in info.full_text.upper()


def test_scanned_pdf_has_no_text():
    info = PDFProcessor().open_info(L09)
    assert not info.has_meaningful_text
    assert info.total_alnum == 0
