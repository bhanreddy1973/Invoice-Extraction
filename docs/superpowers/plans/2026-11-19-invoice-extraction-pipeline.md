# Invoice Extraction Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or implement task-by-task. Steps use checkbox syntax.

**Goal:** Production-grade invoice extraction for Es Magico assignment using NVIDIA Integrate API (Nemotron text + vision model) and Tesseract OCR.

**Architecture:** Document router → PDF text / OCR / vision → NVIDIA LLM → Pydantic + financial validation → eval/batch/cost.

**Tech:** Python 3.11+, PyMuPDF, Pillow, OpenCV, pytesseract, OpenAI-compatible NVIDIA client, Pydantic, FastAPI, pytest.

---

## Task 1: Repo scaffold, gitignore, data layout, git remote

**Files:**
- Create: `.gitignore`, `.env.example`, `requirements.txt`, `README.md` (stub)
- Create: directory tree under `src/`, `api/`, `scripts/`, `tests/`, `outputs/`, `reports/`, `docs/`
- Move: `data/raw_download/labelled/*` docs → `data/raw/labelled/`, JSON → `data/ground_truth/`, unlabelled → `data/raw/unlabelled/`
- Keep pack `schema.json` at `data/schema.json`

- [ ] Create `.gitignore` (exclude `.env`, caches, outputs artifacts as needed, OneDrive junk, `__pycache__`, raw download temp)
- [ ] Create folder structure + `__init__.py` files
- [ ] Relocate dataset into canonical paths
- [ ] `git init`, first commit, remote `origin` → `https://github.com/bhanreddy1973/Invoice-Extraction.git`
- [ ] Push when credentials allow

## Task 2: Config, exceptions, NVIDIA provider

**Files:**
- `src/config.py`, `src/exceptions.py`
- `src/llm/base.py`, `src/llm/provider.py`, `src/llm/prompts.py`
- `src/monitoring/cost_tracker.py`, `src/monitoring/usage_tracker.py`

- [ ] Load env: `NVIDIA_API_KEY`, text model `nvidia/nemotron-3-ultra-550b-a55b`, vision model configurable (Kimi on NVIDIA)
- [ ] OpenAI-compatible client against `https://integrate.api.nvidia.com/v1`
- [ ] Track tokens/latency; document free-tier pricing as $0 with source note

## Task 3: Document processing + OCR routing

**Files:**
- `src/document_processing/*.py`

- [ ] File validation, PDF text, image preprocess, Tesseract OCR, router routes

## Task 4: Extraction + validation

**Files:**
- `src/extraction/*`, `src/validation/*`, `src/pipeline.py`

- [ ] Exact pack schema (nullable quantity), financial Decimal check, retries, review metadata internal

## Task 5: CLI, batch, eval, API

**Files:**
- `extract.py`, `evaluate.py`, `scripts/run_batch.py`, `scripts/generate_report.py`, `api/main.py`

## Task 6: Tests + docs + live run

- [ ] pytest offline with mocks
- [ ] Live batch/eval when API works
- [ ] Reports + README + walkthrough
