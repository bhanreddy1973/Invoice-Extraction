#!/usr/bin/env python3
"""Batch-process all labelled and unlabelled documents."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_settings
from src.pipeline import InvoicePipeline


def _iter_docs(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
    )


def main() -> int:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    pipeline = InvoicePipeline(settings)

    jobs = [
        ("labelled", settings.data_raw_labelled, settings.outputs_labelled),
        ("unlabelled", settings.data_raw_unlabelled, settings.outputs_unlabelled),
    ]

    summary: list[dict] = []
    started = time.perf_counter()

    for label, src, out_dir in jobs:
        out_dir.mkdir(parents=True, exist_ok=True)
        settings.outputs_errors.mkdir(parents=True, exist_ok=True)
        for doc in _iter_docs(src):
            result = pipeline.process(doc)
            record = {
                "set": label,
                "document": doc.name,
                "status": result.status,
                "route": result.route,
                "latency_seconds": result.latency_seconds,
                "model_used": result.model_used,
                "cost": result.cost,
                "error_code": result.error_code,
                "review": result.review,
            }
            summary.append(record)
            if result.invoice is not None:
                target = out_dir / f"{doc.stem}.json"
                target.write_text(json.dumps(result.invoice, indent=2), encoding="utf-8")
                print(f"[OK] {label}/{doc.name} -> {target.name} route={result.route}")
            else:
                err = settings.outputs_errors / f"{doc.stem}.error.json"
                err.write_text(
                    json.dumps(
                        {
                            "document": doc.name,
                            "error_code": result.error_code,
                            "error_message": result.error_message,
                            "route": result.route,
                            "review": result.review,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                print(f"[ERR] {label}/{doc.name} -> {err.name} code={result.error_code}")

    elapsed = time.perf_counter() - started
    summary_path = settings.reports_dir / "batch_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps({"elapsed_seconds": elapsed, "results": summary}, indent=2),
        encoding="utf-8",
    )
    print(f"Batch complete in {elapsed:.1f}s. Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
