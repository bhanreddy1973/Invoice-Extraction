"""FastAPI interface for invoice extraction — same InvoicePipeline as CLI/Streamlit."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.pipeline import InvoicePipeline

logger = logging.getLogger(__name__)
settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Invoice Extraction Pipeline",
    version="0.2.0",
    description="Upload a PDF/image and receive schema-validated invoice JSON.",
)
pipeline = InvoicePipeline(settings)

ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "extraction_mode": settings.extraction_mode,
        "text_model": settings.nvidia_text_model,
        "vision_model": settings.nvidia_vision_model,
        "batch_workers": settings.batch_workers,
        "tesseract_configured": bool(settings.tesseract_cmd),
        "api_key_configured": bool(settings.nvidia_api_key),
    }


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> JSONResponse:
    filename = file.filename or "upload.bin"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "UNSUPPORTED_FORMAT",
                "message": f"Unsupported file type: {suffix or '(none)'}",
            },
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "EMPTY_DOCUMENT", "message": "Uploaded file is empty"},
        )
    if len(data) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "FILE_TOO_LARGE",
                "message": f"File exceeds {settings.max_file_size_mb} MB limit",
            },
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        result = pipeline.process(tmp_path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled extract error for %s", filename)
        raise HTTPException(
            status_code=500,
            detail={"error_code": "PIPELINE_ERROR", "message": "Internal processing error"},
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    body = {
        "status": result.status,
        "document": filename,
        "invoice": result.invoice,
        "validation": {
            "schema_valid": result.schema_valid,
            "financial": result.financial,
        },
        "review": result.review,
        "route": result.route,
        "model_used": result.model_used,
        "latency_seconds": result.latency_seconds,
        "cost": result.cost,
        "notes": result.notes,
        "error_code": result.error_code,
        "error_message": result.error_message,
    }
    # Do not leak stack traces; controlled payload only.
    status_code = 200 if result.status == "success" else 422
    return JSONResponse(content=body, status_code=status_code)
