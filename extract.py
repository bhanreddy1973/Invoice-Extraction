#!/usr/bin/env python3
"""CLI: extract invoice JSON from a single document."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.config import get_settings
from src.pipeline import InvoicePipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract structured invoice JSON from a PDF or image.")
    parser.add_argument("document", type=Path, help="Path to PDF or image")
    parser.add_argument("--output", "-o", type=Path, help="Optional path to write JSON")
    parser.add_argument("--meta", action="store_true", help="Also print processing metadata")
    args = parser.parse_args(argv)

    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    pipeline = InvoicePipeline(settings)
    result = pipeline.process(args.document)

    if result.status != "success" or result.invoice is None:
        payload = {
            "status": "error",
            "error_code": result.error_code,
            "error_message": result.error_message,
        }
        print(json.dumps(payload, indent=2))
        if args.output:
            err_path = args.output.with_suffix(".error.json")
            err_path.parent.mkdir(parents=True, exist_ok=True)
            err_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return 1

    print(json.dumps(result.invoice, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result.invoice, indent=2), encoding="utf-8")
    if args.meta:
        meta = {
            "route": result.route,
            "schema_valid": result.schema_valid,
            "financial": result.financial,
            "review": result.review,
            "latency_seconds": result.latency_seconds,
            "cost": result.cost,
            "model_used": result.model_used,
            "notes": result.notes,
        }
        print(json.dumps(meta, indent=2, default=str), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
