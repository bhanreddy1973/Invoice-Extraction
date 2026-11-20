# Failure Analysis

Updated from the **current** hybrid pipeline (Bolt text → Omni vision escalate, public `unit_price`, qty × unit_price amount priority).

Sources: labelled eval `reports/hybrid_escalate/`, batch `reports/batch_summary.json`, outputs under `outputs/`.

## Summary

| Run | Result |
|---|---|
| Labelled eval (10) | **100%** overall / schema / financial |
| Full batch (20) | **20/20 success**, 0 hard failures |
| Batch wall time | ~90.5 s (`BATCH_WORKERS=10`) |
| API cost | $0 (NVIDIA free-tier catalog models) |

## Historical OCR-first failures (fixed)

Before vision escalate, OCR/text-only labelled accuracy was **70%** (`reports/ocr_baseline/README.md`):

| Doc | Failure mode | Root cause | Fix |
|---|---|---|---|
| **L02.jpg** | `line_items` wrong / null qty | Photo; OCR drops quantities | Escalate OCR → vision |
| **L09.pdf** | wrong tax/total + line amounts | Scan OCR digit errors | Escalate on financial mismatch → vision |
| **L10.pdf** | null / wrong quantities | Scan; OCR weak on item table | Escalate OCR → vision |

With current hybrid+escalate, all three match ground truth (eval exact match).

## Current batch behaviour (20 docs)

### Hard failures

None. All documents wrote JSON under `outputs/labelled` or `outputs/unlabelled`.

### Retries

| Doc | Code | Outcome |
|---|---|---|
| **U02.jpg** | `LLM_PROVIDER_ERROR` (empty NVIDIA content) on attempt 1 | Succeeded on attempt 2 (`route=vision`) |

### Vision escalations

| Doc | Route | Trigger (typical) |
|---|---|---|
| L02.jpg | `ocr->vision` | financial mismatch on OCR first pass |
| L09.pdf | `ocr->vision` | financial mismatch on OCR first pass |
| L10.pdf | `ocr->vision` | financial mismatch on OCR first pass |
| U01.pdf | `pdf_text->vision` | financial mismatch after Bolt |
| U04.pdf | `pdf_text->vision` | financial mismatch after Bolt |
| U05.pdf | `ocr->vision` | OCR confirm / scan path |
| U02.jpg | `vision` | weak OCR → direct vision |

Digital selectable PDFs (most L0x / U0x) stayed on Bolt (`pdf_text`) when financially consistent.

### Review flags (pipeline succeeded, human check recommended)

| Doc | `review_reason` | Notes |
|---|---|---|
| **U02.jpg** | `low_ocr_quality_vision_route` | Photo invoice; vision recovered totals (917) with unit prices |
| **U04.pdf** | `financial_mismatch` | After escalate: line sum `536.1` vs extracted total `528.9` (Δ ≈ 7.2); possible fee/discount outside rows. Flagged, not dropped |

Non-invoices classified correctly: **L08**, **U06**, **U10** (`is_invoice: false`, other fields null).

## Unit price / amount priority

- Schema now includes nullable `unit_price` on each line item.
- When qty and unit_price both present → `amount = qty × unit_price` (2 dp) before invoice-level total check.
- Example: U02 gloves corrected via `6 × 64 = 384` (previously mis-extracted as 364 → financial fail).
- Labelled eval ignores `unit_price` vs GT (GT has no unit_price); compares description / quantity / amount only.

## Error-handling coverage exercised

| Mechanism | Observed |
|---|---|
| Typed provider empty content | U02 retry |
| JSON parse retry | U07 had a first-pass parse warning; recovered |
| Vision escalate on financial fail | L02/L09/L10/U01/U04 |
| Parallel batch isolation | One doc retry did not stop others |
| `needs_review` without abort | U02, U04 |

## Residual risks / not fixed

1. **U04 residual mismatch** — qty×rate lines are internally consistent but disagree with printed total; needs human review or broader fee/discount rules.
2. **Provider flakiness** — empty LLM content (U02) requires retries; keep `BATCH_RETRIES≥2`.
3. **OCR alone remains insufficient** on photos/scans — do not disable vision escalate.
4. **Historical `ocr_baseline` JSON** may have been overwritten by an earlier hybrid eval run; treat `ocr_baseline/README.md` + `mode_comparison.md` as the 70% snapshot narrative.

## Recommendations

1. Keep hybrid escalate + unit_price priority as default.
2. Surface `amount_corrections` / financial Δ in Streamlit review UI for U04-like cases.
3. Optionally add discount/fee line heuristics when `|sum(lines)+tax − total|` is small but nonzero after escalate.
