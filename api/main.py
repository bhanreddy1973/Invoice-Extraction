"""FastAPI interface for invoice extraction."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.pipeline import InvoicePipeline

app = FastAPI(title="Invoice Extraction Pipeline", version="0.1.0")
settings = get_settings()
pipeline = InvoicePipeline(settings)

ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "text_model": settings.nvidia_text_model,
        "vision_model": settings.nvidia_vision_model,
        "tesseract_configured": bool(settings.tesseract_cmd),
    }


@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> JSONResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(status_code=400, detail={"error_code": "UNSUPPORTED_FORMAT", "message": "Unsupported file type"})

    data = await file.read()
    if len(data) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail={"error_code": "FILE_TOO_LARGE", "message": "File too large"})

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        result = pipeline.process(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    body = {
        "status": result.status,
        "invoice": result.invoice,
        "validation": {
            "schema_valid": result.schema_valid,
            "financial": result.financial,
        },
        "review": result.review,
        "route": result.route,
        "model_used": result.model_used,
        "error_code": result.error_code,
        "error_message": result.error_message,
    }
    status_code = 200 if result.status == "success" else 422
    return JSONResponse(content=body, status_code=status_code)
