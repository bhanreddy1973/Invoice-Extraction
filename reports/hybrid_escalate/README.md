# Hybrid + vision escalate results (current)

## Strategy

1. Digital PDF text / OCR text → fast `nvidia/nemotron-3.5-bolt-e4b`
2. Escalate to `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` when:
   - critical fields missing
   - financial check fails
   - OCR null quantities
   - or route is `ocr` (confirm scans/photos with vision)
3. Public nullable `unit_price`; when qty + unit_price present → `amount = qty × unit_price`

## Labelled eval (10 docs) — refreshed

| Metric | OCR-only Bolt (historical) | Hybrid + escalate (current) |
|---|---:|---:|
| Overall accuracy | 70% | **100%** |
| line_items | 70% | **100%** |
| tax_total / total | 90% | **100%** |
| Avg latency | ~7.5 s | **~13.3 s** |
| Total input tokens | 10,662 | **19,912** |
| Total output tokens | 4,160 | **9,280** |
| API cost USD | 0 | **0** |

Escalated labelled docs: **L02, L09, L10** (`ocr->vision`). Digital PDFs stayed on Bolt when financially consistent.

Files: `evaluation_results.json`, `evaluation_report.md` / `evaluation_results.md`
