# Invoice Extraction Pipeline

Es Magico AI Internship Assignment — production-style invoice extraction with validation, evaluation, cost tracking, and bad-input handling.

## Problem

Finance teams receive mixed vendor documents (digital PDFs, scans, photos, and non-invoices). This pipeline:

1. Classifies whether a document is an invoice
2. Extracts structured fields into the assignment JSON schema
3. Validates schema + financial consistency
4. Evaluates against labelled ground truth
5. Reports API usage/cost honestly

## Architecture (short)

```
Upload → File validation → Router (pdf_text | ocr | vision)
      → NVIDIA LLM extraction → Pydantic schema check
      → Financial check → JSON output + metrics
```

See `docs/ARCHITECTURE.md` for the full diagram and component notes.

## Technology stack

| Component | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Document/OCR ecosystem, Pydantic, FastAPI |
| PDF | PyMuPDF | Fast text extract + page render |
| Images | Pillow + OpenCV | Load/preprocess without destroying signal |
| OCR | Tesseract (`pytesseract`) | Local, free fallback for scans/photos |
| LLM | NVIDIA Integrate API | Free catalog models; OpenAI-compatible client |
| Text model | `nvidia/nemotron-3-ultra-550b-a55b` | Structured extraction from OCR/digital text |
| Vision model | `moonshotai/kimi-k3.1-pro` | Layout-aware fallback for weak OCR |
| Validation | Pydantic v2 | Exact pack schema + clear errors |
| API | FastAPI | Optional upload endpoint |
| Eval | pandas + stdlib + Decimal | Field metrics without float money bugs |

## Prerequisites

- Python 3.11+
- Tesseract OCR (Windows default path supported: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- NVIDIA API key with Integrate access

## Installation

```bash
git clone https://github.com/bhanreddy1973/Invoice-Extraction.git
cd Invoice-Extraction
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Set `NVIDIA_API_KEY` in `.env`.

## Commands

Single document:

```bash
python extract.py data/raw/labelled/L01.pdf
python extract.py data/raw/labelled/L01.pdf --output outputs/labelled/L01.json --meta
```

Evaluate 10 labelled documents:

```bash
python evaluate.py
```

Batch all 20 documents:

```bash
python scripts/run_batch.py
python scripts/generate_report.py
```

API:

```bash
uvicorn api.main:app --reload
```

Tests (no API key required for unit suite):

```bash
pytest -q
```

## Output schema

Matches `data/schema.json` from the Es Magico sample pack (nullable `quantity`, non-invoice nulls, ISO dates, ISO currency codes).

## Model selection rationale

- **Nemotron (text)** for digital PDFs and strong OCR text: cheaper/faster path than sending every page as vision.
- **Kimi vision on NVIDIA** when embedded text is missing or OCR is weak (scans/photos).
- Provider abstraction lives in `src/llm/` so models can change via `.env` without pipeline rewrites.

## Cost methodology

Configured free-tier catalog prices are **$0 / 1M tokens** for the selected models (recorded in `src/monitoring/cost_tracker.py` with source + date). Token counts come from provider usage when available. Local Tesseract compute is excluded from API cost.

## Known limitations

- Free NVIDIA models may throttle or change availability.
- Line-item matching in eval is order-sensitive and exact after light normalization (no fuzzy vendor/description awards).
- Ambiguous financial mismatches (fees outside line tables) are flagged for review rather than silently forced to pass.

## Dataset

Sample pack mirrored under `data/raw/` and `data/ground_truth/`. Inventory: `docs/DATASET_INVENTORY.md`.
