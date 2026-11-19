"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings for extraction, OCR, and NVIDIA API access."""

    nvidia_api_key: str
    nvidia_base_url: str
    nvidia_text_model: str
    nvidia_vision_model: str
    max_file_size_mb: int
    pdf_text_alnum_threshold: int
    financial_tolerance: Decimal
    llm_max_retries: int
    llm_timeout_seconds: float
    ocr_language: str
    tesseract_cmd: str | None
    log_level: str
    enable_thinking: bool
    data_raw_labelled: Path
    data_raw_unlabelled: Path
    data_ground_truth: Path
    outputs_labelled: Path
    outputs_unlabelled: Path
    outputs_errors: Path
    reports_dir: Path

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def get_settings() -> Settings:
    """Load settings from environment with project defaults."""
    tesseract = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tesseract and not Path(tesseract).exists():
        tesseract = None

    return Settings(
        nvidia_api_key=os.getenv("NVIDIA_API_KEY", ""),
        nvidia_base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        nvidia_text_model=os.getenv("NVIDIA_TEXT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
        nvidia_vision_model=os.getenv("NVIDIA_VISION_MODEL", "moonshotai/kimi-k3.1-pro"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "20")),
        pdf_text_alnum_threshold=int(os.getenv("PDF_TEXT_ALNUM_THRESHOLD", "80")),
        financial_tolerance=Decimal(os.getenv("FINANCIAL_TOLERANCE", "0.05")),
        llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "120")),
        ocr_language=os.getenv("OCR_LANGUAGE", "eng"),
        tesseract_cmd=tesseract,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        enable_thinking=_bool(os.getenv("NVIDIA_ENABLE_THINKING"), default=False),
        data_raw_labelled=PROJECT_ROOT / "data" / "raw" / "labelled",
        data_raw_unlabelled=PROJECT_ROOT / "data" / "raw" / "unlabelled",
        data_ground_truth=PROJECT_ROOT / "data" / "ground_truth",
        outputs_labelled=PROJECT_ROOT / "outputs" / "labelled",
        outputs_unlabelled=PROJECT_ROOT / "outputs" / "unlabelled",
        outputs_errors=PROJECT_ROOT / "outputs" / "errors",
        reports_dir=PROJECT_ROOT / "reports",
    )
