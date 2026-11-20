from pathlib import Path

import pytest

from src.config import get_settings
from src.document_processing.document_router import DocumentRouter
from src.exceptions import UnsupportedFormatError, FileTooLargeError
from src.monitoring.cost_tracker import CostTracker
from src.llm.base import LLMUsage


def test_unsupported_format(tmp_path: Path):
    bad = tmp_path / "note.txt"
    bad.write_text("hello", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError):
        DocumentRouter(get_settings()).route(bad)


def test_file_too_large(tmp_path: Path):
    from dataclasses import replace

    tiny = replace(get_settings(), max_file_size_mb=0)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 tiny")
    with pytest.raises(FileTooLargeError):
        DocumentRouter(tiny).route(pdf)


def test_cost_free_tier():
    usage = LLMUsage(provider="nvidia", model="z-ai/glm-5.3-flash", input_tokens=1000, output_tokens=200)
    est = CostTracker().estimate(usage)
    assert est.cost_usd == 0.0
