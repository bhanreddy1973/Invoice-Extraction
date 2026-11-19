"""Decide how each uploaded document should be processed."""

from __future__ import annotations

import logging
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path

from src.config import Settings, get_settings
from src.document_processing.image_processor import ImageProcessor
from src.document_processing.ocr_processor import OCRProcessor
from src.document_processing.pdf_processor import PDFProcessor
from src.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFormatError,
    UnreadableDocumentError,
)

logger = logging.getLogger(__name__)

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


@dataclass
class RoutedDocument:
    path: Path
    route: str  # pdf_text | ocr | vision | unreadable
    text: str | None = None
    images_png: list[bytes] = field(default_factory=list)
    page_count: int = 0
    ocr_alnum: int = 0
    notes: list[str] = field(default_factory=list)


class DocumentRouter:
    """Validate files and select pdf_text / ocr / vision routes."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.pdf = PDFProcessor(alnum_threshold=self.settings.pdf_text_alnum_threshold)
        self.images = ImageProcessor()
        self.ocr = OCRProcessor(
            language=self.settings.ocr_language,
            tesseract_cmd=self.settings.tesseract_cmd,
        )

    def route(self, path: Path) -> RoutedDocument:
        path = Path(path)
        self._validate_file(path)
        suffix = path.suffix.lower()

        if suffix in PDF_EXTENSIONS:
            return self._route_pdf(path)
        if suffix in IMAGE_EXTENSIONS:
            return self._route_image(path)
        raise UnsupportedFormatError(f"Unsupported file type: {suffix or '(none)'}")

    def _validate_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise UnsupportedFormatError(f"File not found: {path}")
        size = path.stat().st_size
        if size <= 0:
            raise EmptyDocumentError(f"File is empty: {path.name}")
        if size > self.settings.max_file_size_bytes:
            raise FileTooLargeError(
                f"File exceeds {self.settings.max_file_size_mb} MB limit: {path.name}"
            )
        suffix = path.suffix.lower()
        if suffix not in PDF_EXTENSIONS | IMAGE_EXTENSIONS:
            mime, _ = mimetypes.guess_type(str(path))
            raise UnsupportedFormatError(
                f"Unsupported format for {path.name} (suffix={suffix}, mime={mime})"
            )

    def _route_pdf(self, path: Path) -> RoutedDocument:
        info = self.pdf.open_info(path)
        if info.has_meaningful_text:
            return RoutedDocument(
                path=path,
                route="pdf_text",
                text=info.full_text,
                page_count=info.page_count,
                notes=[f"embedded_alnum={info.total_alnum}"],
            )

        notes = [f"embedded_alnum={info.total_alnum}", "falling_back_to_ocr"]
        png_pages = self.pdf.render_pages(path)
        ocr_chunks: list[str] = []
        total_alnum = 0
        for png in png_pages:
            image = self.images.load_png_bytes(png)
            prepared = self.images.preprocess_for_ocr(image)
            result = self.ocr.extract(prepared)
            ocr_chunks.append(result.text)
            total_alnum += result.alnum_count

        combined = "\n\n".join(chunk for chunk in ocr_chunks if chunk).strip()
        if total_alnum >= self.settings.pdf_text_alnum_threshold:
            return RoutedDocument(
                path=path,
                route="ocr",
                text=combined,
                images_png=png_pages,
                page_count=info.page_count,
                ocr_alnum=total_alnum,
                notes=notes + [f"ocr_alnum={total_alnum}"],
            )

        # Vision fallback for weak OCR
        notes.append(f"ocr_alnum={total_alnum}")
        notes.append("falling_back_to_vision")
        if not png_pages:
            raise UnreadableDocumentError(f"No readable content in PDF: {path.name}")
        return RoutedDocument(
            path=path,
            route="vision",
            text=combined or None,
            images_png=png_pages,
            page_count=info.page_count,
            ocr_alnum=total_alnum,
            notes=notes,
        )

    def _route_image(self, path: Path) -> RoutedDocument:
        image = self.images.load(path)
        png = self.images.to_png_bytes(image)
        prepared = self.images.preprocess_for_ocr(image)
        result = self.ocr.extract(prepared)
        notes = [f"ocr_alnum={result.alnum_count}"]
        if result.alnum_count >= self.settings.pdf_text_alnum_threshold:
            return RoutedDocument(
                path=path,
                route="ocr",
                text=result.text,
                images_png=[png],
                page_count=1,
                ocr_alnum=result.alnum_count,
                notes=notes,
            )
        notes.append("falling_back_to_vision")
        return RoutedDocument(
            path=path,
            route="vision",
            text=result.text or None,
            images_png=[png],
            page_count=1,
            ocr_alnum=result.alnum_count,
            notes=notes,
        )
