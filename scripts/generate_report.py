#!/usr/bin/env python3
"""Generate cost analysis markdown from batch_summary.json if present."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_settings
from src.monitoring.cost_tracker import PRICING_EFFECTIVE_DATE, PRICING_SOURCE


def main() -> int:
    settings = get_settings()
    summary_path = settings.reports_dir / "batch_summary.json"
    if not summary_path.exists():
        print(f"Missing {summary_path}. Run scripts/run_batch.py first.")
        return 1

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    results = data.get("results", [])
    costs = [r.get("cost", {}) for r in results if r.get("cost")]
    total_cost = sum(c.get("cost_usd", 0.0) for c in costs)
    total_in = sum(c.get("input_tokens", 0) for c in costs)
    total_out = sum(c.get("output_tokens", 0) for c in costs)
    n = len(results) or 1
    avg_latency = sum(r.get("latency_seconds", 0.0) for r in results) / n

    lines = [
        "# Cost Analysis",
        "",
        f"- Provider: NVIDIA Integrate API (`{settings.nvidia_base_url}`)",
        f"- Text model: `{settings.nvidia_text_model}`",
        f"- Vision model: `{settings.nvidia_vision_model}`",
        f"- Pricing source: {PRICING_SOURCE}",
        f"- Pricing effective date: {PRICING_EFFECTIVE_DATE.isoformat()}",
        "",
        "## Observed usage (from batch run)",
        "",
        f"- Documents processed: {len(results)}",
        f"- Total input tokens (reported): {total_in}",
        f"- Total output tokens (reported): {total_out}",
        f"- Total API cost (USD): {total_cost:.6f}",
        f"- Average cost per document (USD): {total_cost / n:.6f}",
        f"- Average latency (s): {avg_latency:.2f}",
        "",
        "## Methodology",
        "",
        "Cost = (input_tokens / 1e6 * input_price) + (output_tokens / 1e6 * output_price).",
        "Configured free-tier prices are $0.00 / 1M tokens for the selected NVIDIA catalog models.",
        "Local Tesseract OCR compute is excluded from API cost.",
        "Token counts are taken from provider usage when returned; missing values are recorded as 0 and flagged.",
        "",
    ]
    out = settings.reports_dir / "cost_analysis.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
