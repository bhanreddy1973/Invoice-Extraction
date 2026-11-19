# Implementation Progress Checklist

| Phase | Description | Status | Evidence |
|---|---|---|---|
| 0 | Dataset inspection | Complete | `docs/DATASET_INVENTORY.md`; data under `data/raw` + `data/ground_truth` |
| 1 | Project initialization and architecture | Complete | Structure, `.gitignore`, NVIDIA `.env.example`, README |
| 2 | PDF and image processing | Complete | `src/document_processing/pdf_processor.py`, `image_processor.py` |
| 3 | OCR and document routing | Complete | Tesseract + `document_router.py` (pdf_text/ocr/vision) |
| 4 | LLM integration and extraction | Complete | NVIDIA Nemotron + Kimi vision provider |
| 5 | Structured response parsing | Complete | `response_parser.py` |
| 6 | Pydantic validation | Complete | Pack schema with nullable quantity |
| 7 | Financial validation | Complete | Decimal + tolerance |
| 8 | Error handling and retry strategy | Complete | Typed errors + bounded retries |
| 9 | Evaluation framework | Complete | `evaluate.py` |
| 10 | Batch processing | Complete | `scripts/run_batch.py` |
| 11 | Cost tracking | Complete | Free-tier $0 table + usage tracker |
| 12 | Failure analysis and reporting | Pending | Needs live eval results |
| 13 | FastAPI interface | Complete | `api/main.py` |
| 14 | Testing and integration | Partial | Unit tests passing; live LLM integration pending |
| 15 | README and final verification | Partial | README present; live batch/eval pending |
| 16 | Optional bonus features | Partial | Review metadata in pipeline; Streamlit not yet |

## Phase 0 exit criteria

- [x] Inspect project directory
- [x] Locate 20 sample documents
- [x] Identify labelled vs unlabelled
- [x] Inspect ground-truth / schema format
- [x] Identify formats and page counts
- [x] Determine selectable-text vs scanned
- [x] Identify known non-invoices (labelled L08; candidates U06/U10)
- [x] Document GT ↔ source mapping
- [x] Produce `docs/DATASET_INVENTORY.md`
- [x] Produce `docs/ASSUMPTIONS.md`
- [ ] Confirm LLM provider + API credentials with user (blocker for live eval)
- [ ] Verify Tesseract availability on host (blocker for OCR route)

## Blockers before claiming assignment complete

1. LLM API key / provider choice
2. Tesseract (or documented vision-only fallback for scans)
3. Actual evaluation / batch / cost runs (no fabricated metrics)
