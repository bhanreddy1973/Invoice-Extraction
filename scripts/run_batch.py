#!/usr/bin/env python3
"""Batch-process all labelled and unlabelled documents (optional parallel workers)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Settings, get_settings
from src.pipeline import InvoicePipeline, PipelineResult

# Transient failures worth retrying mid-batch.
RETRYABLE_CODES = {
    "LLM_TIMEOUT",
    "LLM_RATE_LIMIT",
    "LLM_PROVIDER_ERROR",
}

print_lock = threading.Lock()


def _iter_docs(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
    )


@dataclass
class Job:
    label: str
    path: Path
    out_dir: Path
    index: int
    total: int


def _status(msg: str) -> None:
    with print_lock:
        print(msg, flush=True)


def _is_retryable(result: PipelineResult) -> bool:
    if result.status == "success" and result.invoice is not None:
        return False
    return (result.error_code or "") in RETRYABLE_CODES


def _process_one(
    job: Job,
    *,
    settings: Settings,
    max_retries: int,
    retry_backoff_seconds: float,
) -> dict:
    """Process one document with bounded retries. Failures do not stop the batch."""
    # One pipeline per worker call keeps clients/usage trackers thread-isolated.
    pipeline = InvoicePipeline(settings)
    attempts = 0
    result: PipelineResult | None = None
    last_error: str | None = None

    while attempts <= max_retries:
        attempts += 1
        _status(
            f"[{job.index}/{job.total}] START {job.label}/{job.path.name}"
            + (f" (attempt {attempts}/{max_retries + 1})" if attempts > 1 else "")
        )
        try:
            result = pipeline.process(job.path)
        except Exception as exc:  # noqa: BLE001 - keep batch alive
            last_error = f"{type(exc).__name__}: {exc}"
            _status(f"[{job.index}/{job.total}] RETRY {job.label}/{job.path.name} unexpected={last_error}")
            if attempts <= max_retries:
                time.sleep(retry_backoff_seconds * attempts)
                continue
            result = None
            break

        if result.status == "success" and result.invoice is not None:
            break
        if _is_retryable(result) and attempts <= max_retries:
            _status(
                f"[{job.index}/{job.total}] RETRY {job.label}/{job.path.name} "
                f"code={result.error_code} attempt={attempts}/{max_retries + 1}"
            )
            time.sleep(retry_backoff_seconds * attempts)
            continue
        break

    job.out_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_errors.mkdir(parents=True, exist_ok=True)

    if result is not None and result.invoice is not None:
        target = job.out_dir / f"{job.path.stem}.json"
        target.write_text(json.dumps(result.invoice, indent=2), encoding="utf-8")
        _status(
            f"[{job.index}/{job.total}] OK   {job.label}/{job.path.name} "
            f"-> {target.name} route={result.route} model={result.model_used} "
            f"latency={result.latency_seconds:.1f}s attempts={attempts}"
        )
        return {
            "set": job.label,
            "document": job.path.name,
            "status": result.status,
            "route": result.route,
            "latency_seconds": result.latency_seconds,
            "model_used": result.model_used,
            "cost": result.cost,
            "error_code": result.error_code,
            "review": result.review,
            "attempts": attempts,
        }

    error_code = result.error_code if result else "UNEXPECTED_EXCEPTION"
    error_message = result.error_message if result else last_error
    err = settings.outputs_errors / f"{job.path.stem}.error.json"
    err.write_text(
        json.dumps(
            {
                "document": job.path.name,
                "error_code": error_code,
                "error_message": error_message,
                "route": result.route if result else None,
                "review": result.review if result else None,
                "attempts": attempts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _status(
        f"[{job.index}/{job.total}] ERR  {job.label}/{job.path.name} "
        f"-> {err.name} code={error_code} attempts={attempts}"
    )
    return {
        "set": job.label,
        "document": job.path.name,
        "status": "error",
        "route": result.route if result else None,
        "latency_seconds": result.latency_seconds if result else None,
        "model_used": result.model_used if result else None,
        "cost": result.cost if result else None,
        "error_code": error_code,
        "review": result.review if result else None,
        "attempts": attempts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch invoice extraction with optional parallelism.")
    settings = get_settings()
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Parallel workers (1 = sequential). Default from BATCH_WORKERS env: {settings.batch_workers}",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help=f"Extra retries per document on timeout/rate-limit/provider errors. Default: {settings.batch_retries}",
    )
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=None,
        help=f"Base backoff seconds between retries. Default: {settings.batch_retry_backoff_seconds}",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=settings.log_level)
    workers = max(1, args.workers if args.workers is not None else settings.batch_workers)
    retries = args.retries if args.retries is not None else settings.batch_retries
    retry_backoff = (
        args.retry_backoff if args.retry_backoff is not None else settings.batch_retry_backoff_seconds
    )

    jobs_spec = [
        ("labelled", settings.data_raw_labelled, settings.outputs_labelled),
        ("unlabelled", settings.data_raw_unlabelled, settings.outputs_unlabelled),
    ]

    jobs: list[Job] = []
    all_docs: list[tuple[str, Path, Path]] = []
    for label, src, out_dir in jobs_spec:
        for doc in _iter_docs(src):
            all_docs.append((label, doc, out_dir))
    total = len(all_docs)
    for i, (label, doc, out_dir) in enumerate(all_docs, start=1):
        jobs.append(Job(label=label, path=doc, out_dir=out_dir, index=i, total=total))

    _status(
        f"Batch starting: {total} documents | workers={workers} | "
        f"retries={retries} | mode={settings.extraction_mode}"
    )

    summary: list[dict] = []
    started = time.perf_counter()
    ok = 0
    err = 0

    if workers == 1:
        for job in jobs:
            record = _process_one(
                job,
                settings=settings,
                max_retries=retries,
                retry_backoff_seconds=retry_backoff,
            )
            summary.append(record)
            if record["status"] == "success":
                ok += 1
            else:
                err += 1
            _status(f"Progress: {ok + err}/{total} complete (ok={ok} err={err})")
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    _process_one,
                    job,
                    settings=settings,
                    max_retries=retries,
                    retry_backoff_seconds=retry_backoff,
                ): job
                for job in jobs
            }
            for future in as_completed(futures):
                job = futures[future]
                try:
                    record = future.result()
                except Exception as exc:  # noqa: BLE001
                    err += 1
                    record = {
                        "set": job.label,
                        "document": job.path.name,
                        "status": "error",
                        "route": None,
                        "latency_seconds": None,
                        "model_used": None,
                        "cost": None,
                        "error_code": "WORKER_CRASH",
                        "review": None,
                        "attempts": 0,
                        "worker_error": str(exc),
                    }
                    _status(f"[{job.index}/{total}] ERR  worker crash on {job.path.name}: {exc}")
                else:
                    if record["status"] == "success":
                        ok += 1
                    else:
                        err += 1
                summary.append(record)
                _status(f"Progress: {ok + err}/{total} complete (ok={ok} err={err})")

    # Stable summary order by original job index
    order = {job.path.name: job.index for job in jobs}
    summary.sort(key=lambda r: order.get(r["document"], 10_000))

    elapsed = time.perf_counter() - started
    summary_path = settings.reports_dir / "batch_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "elapsed_seconds": elapsed,
                "workers": workers,
                "retries": retries,
                "ok": ok,
                "err": err,
                "results": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _status(
        f"Batch complete in {elapsed:.1f}s | ok={ok} err={err} | "
        f"workers={workers} | Summary: {summary_path}"
    )
    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
