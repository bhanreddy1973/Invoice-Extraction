"""PDF opening, text extraction, and page rendering via PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from src.exceptions import CorruptFileError, EmptyDocumentError


@dataclass
class PDFPageInfo:
    page_number: int
    text: str
    alnum_count: int


@dataclass
class PDFDocumentInfo:
    path: Path
    page_count: int
    pages: list[PDFPageInfo]
    full_text: str
    total_alnum: int
    has_meaningful_text: bool


def _alnum_count(text: str) -> int:
    return sum(c.isalnum() for c in text)


class PDFProcessor:
    """Extract embedded text and optionally render pages to images."""

    def __init__(self, alnum_threshold: int = 80) -> None:
        self.alnum_threshold = alnum_threshold

    def open_info(self, path: Path) -> PDFDocumentInfo:
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001 - surface as corrupt
            raise CorruptFileError(f"Unable to open PDF: {path.name}") from exc

        if doc.page_count == 0:
            doc.close()
            raise EmptyDocumentError(f"PDF has zero pages: {path.name}")

        pages: list[PDFPageInfo] = []
        texts: list[str] = []
        total_alnum = 0
        try:
            for index, page in enumerate(doc):
                text = page.get_text("text") or ""
                count = _alnum_count(text)
                total_alnum += count
                pages.append(PDFPageInfo(page_number=index + 1, text=text, alnum_count=count))
                texts.append(text)
        finally:
            doc.close()

        full_text = "\n".join(texts).strip()
        return PDFDocumentInfo(
            path=path,
            page_count=len(pages),
            pages=pages,
            full_text=full_text,
            total_alnum=total_alnum,
            has_meaningful_text=total_alnum >= self.alnum_threshold,
        )

    def render_pages(self, path: Path, *, dpi: int = 150, max_pages: int = 5) -> list[bytes]:
        """Render PDF pages to PNG bytes for OCR or vision."""
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001
            raise CorruptFileError(f"Unable to open PDF for rendering: {path.name}") from exc

        images: list[bytes] = []
        try:
            zoom = dpi / 72.0
            matrix = pymupdf.Matrix(zoom, zoom)
            for index, page in enumerate(doc):
                if index >= max_pages:
                    break
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                images.append(pix.tobytes("png"))
        finally:
            doc.close()

        if not images:
            raise EmptyDocumentError(f"No pages rendered from PDF: {path.name}")
        return images
