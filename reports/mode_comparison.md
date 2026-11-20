# Mode comparison (current stack)

## OCR / text first without vision escalate (historical)

Path: `reports/ocr_baseline/` (see README snapshot; do not overwrite with current hybrid)

| Metric | Value |
|---|---:|
| Overall accuracy | 70.0% |
| line_items | 70.0% |
| tax_total / total | 90.0% |
| Schema success | 100.0% |
| Financial success | 90.0% |

Failed docs: **L02** (quantities), **L09** (OCR digit errors → wrong tax/total), **L10** (quantities).

## Vision mode (OCR disabled)

Path: `reports/vision_no_ocr/`

| Metric | Value |
|---|---:|
| Overall accuracy | **100.0%** |
| All fields | **100.0%** |
| Avg latency (s) | ~12.2 |
| API cost USD | 0 |

## Hybrid + vision escalate + unit_price (current default)

Path: `reports/hybrid_escalate/`, top-level `reports/evaluation_report.md`

| Metric | Value |
|---|---:|
| Overall accuracy | **100.0%** |
| Schema / financial success | **100.0%** |
| Avg latency (s) | **13.32** |
| Input / output tokens | 19,912 / 9,280 |
| API cost USD | **0** |

Batch (20 docs, `BATCH_WORKERS=10`): **20/20 ok**, ~90.5 s wall, ~15.4 s avg latency/doc, tokens in/out 39,259 / 17,060. See `reports/failure_analysis.md` and `reports/cost_analysis.md`.

## Takeaway

OCR alone is not enough for scans/photos. Hybrid Bolt + Omni escalate recovers labelled accuracy to 100% with modest extra latency/tokens. `unit_price` + qty×rate priority reduces silent amount errors (e.g. U02 gloves).
