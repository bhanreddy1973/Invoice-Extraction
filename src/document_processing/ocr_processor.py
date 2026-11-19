"""Tesseract OCR wrapper."""

from __future__ import annotations

from dataclasses import dataclass

import pytesseract
from PIL import Image

from src.exceptions import UnreadableDocumentError


@dataclass
class OCRResult:
    text: str
    alnum_count: int
    confidence_mean: float | None
    engine: str = "tesseract"


class OCRProcessor:
    """Run Tesseract on preprocessed images."""

    def __init__(self, *, language: str = "eng", tesseract_cmd: str | None = None) -> None:
        self.language = language
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract(self, image: Image.Image) -> OCRResult:
        try:
            text = pytesseract.image_to_string(image, lang=self.language) or ""
            conf = self._mean_confidence(image)
        except pytesseract.TesseractNotFoundError as exc:
            raise UnreadableDocumentError(
                "Tesseract OCR is not installed or TESSERACT_CMD is incorrect"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise UnreadableDocumentError(f"OCR failed: {exc}") from exc

        cleaned = text.strip()
        alnum = sum(c.isalnum() for c in cleaned)
        return OCRResult(text=cleaned, alnum_count=alnum, confidence_mean=conf)

    def _mean_confidence(self, image: Image.Image) -> float | None:
        try:
            data = pytesseract.image_to_data(image, lang=self.language, output_type=pytesseract.Output.DICT)
            confs = [float(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and float(c) >= 0]
            if not confs:
                return None
            return sum(confs) / len(confs)
        except Exception:  # noqa: BLE001
            return None
