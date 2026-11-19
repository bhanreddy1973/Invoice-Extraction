"""Image loading and light preprocessing for OCR."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from src.exceptions import CorruptFileError, EmptyDocumentError


class ImageProcessor:
    """Load images and apply conservative preprocessing."""

    SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}

    def load(self, path: Path) -> Image.Image:
        try:
            image = Image.open(path)
            image.load()
        except Exception as exc:  # noqa: BLE001
            raise CorruptFileError(f"Unable to open image: {path.name}") from exc
        if image.width == 0 or image.height == 0:
            raise EmptyDocumentError(f"Empty image: {path.name}")
        return image.convert("RGB")

    def to_png_bytes(self, image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """Denoise + adaptive threshold when contrast is poor; otherwise return RGB."""
        rgb = np.array(image.convert("RGB"))
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        mean = float(np.mean(gray))
        std = float(np.std(gray))

        # Skip aggressive transforms on already-clear scans
        if std > 45 and 40 < mean < 220:
            return image.convert("RGB")

        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        return Image.fromarray(binary).convert("RGB")

    def load_png_bytes(self, data: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(data))
            image.load()
        except Exception as exc:  # noqa: BLE001
            raise CorruptFileError("Unable to decode rendered page image") from exc
        return image.convert("RGB")
