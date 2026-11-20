# Evaluation Report (historical OCR / text hybrid — no vision escalate)

**Snapshot narrative** (do not confuse with current `reports/hybrid_escalate/`).  
Full field-level JSON for this 70% run may have been overwritten; use this report + `README.md` as the baseline record.

```text
=========================================
INVOICE EXTRACTION EVALUATION
=========================================

Mode: hybrid (OCR/text first, no vision escalate)
Documents evaluated: 10

FIELD LEVEL ACCURACY (snapshot)

Field             Accuracy
-----------------------------------------
Overall           70.0%
line_items        70.0%
tax_total         90.0%
total             90.0%
-----------------------------------------
Schema success rate: 100.0%
Financial success rate: 90.0%

Failed docs: L02, L09, L10
=========================================
```
