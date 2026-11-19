# Assumptions Log

All decisions not explicitly fixed by the Es Magico assignment PDF or the sample pack are recorded here.

| ID | Assumption | Reason | Impact | Needs confirmation | How handled |
|---|---|---|---|---|---|
| A01 | Pack `schema.json` is the canonical output schema (including nullable `quantity`). | Pack ships an explicit JSON Schema; assignment example is illustrative. | Pydantic models must allow `quantity: null`. | No | Follow pack schema; document in README. |
| A02 | Labelled files map by stem (`L01.pdf` ↔ `L01.json`). | Pack README states this. | Eval harness pairing. | No | Implement stem matching. |
| A03 | Meaningful digital text requires ≥ ~80 alphanumeric characters from PyMuPDF. | Avoid treating metadata crumbs as extractable text. | Routing: `pdf_text` vs OCR/vision. | Soft | Configurable threshold; logged per document. |
| A04 | Bad-input scenario beyond non-invoice = unreadable / insufficient OCR+vision content. | Assignment asks to pick one extra bad case; master prompt recommends unreadable. | Error taxonomy includes `UNREADABLE_DOCUMENT`. | No | Implement as specified. |
| A05 | Local OCR compute cost is excluded from API cost reports. | Assignment asks for API cost; OCR is local. | Cost analysis states exclusion. | No | Document in cost report. |
| A06 | LLM provider is NVIDIA Integrate API with text model `nvidia/nemotron-3-ultra-550b-a55b` and vision model `moonshotai/kimi-k3.1-pro`. | User-selected free NVIDIA/Nemotron stack with provided Integrate examples. | Provider module, pricing table, README. | No (confirmed) | Implemented in `src/llm/provider.py` + `.env.example`. |
| A11 | Free-tier token prices are recorded as $0.00 pending paid SKU use. | User specified NVIDIA free models. | Cost reports show $0 with documented source/date. | Soft — confirm if entitlement changes | `src/monitoring/cost_tracker.py` |
| A07 | Synthetic unit fixtures may be used when API keys are absent; live eval is separate. | Assignment forbids committing keys; tests must run offline. | CI/local pytest without charges. | No | Mock LLM in unit/integration tests. |
| A08 | Unlabelled U06/U10 are non-invoices based on text preview only. | No GT provided. | Must not claim accuracy on them. | N/A | Classify via pipeline; no fabricated GT. |
| A09 | Python 3.11+; workspace currently runs Python 3.12. | Master prompt stack. | Type hints / tooling. | No | Target 3.11+ in README. |
| A10 | Do not tune prompts solely against labelled docs without disclosure. | Assignment ground rule on overfitting. | Report must disclose any labelled-set tuning. | No | Prefer generic prompts; disclose if tuned. |
