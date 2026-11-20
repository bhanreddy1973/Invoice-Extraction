# OCR baseline evaluation (stored)

This folder stores the labelled-set evaluation that used the **hybrid** pipeline:

- digital PDFs → embedded text + Nemotron
- scans/photos → **Tesseract OCR** (+ vision only if OCR text was too weak)

## Snapshot results

- Documents: 10
- Overall accuracy: **70.0%**
- `line_items`: 70% (failures: L02, L09, L10)
- `tax_total` / `total`: 90% (failure: L09)
- Schema success: 100%
- Financial success: 90%

Files:

- `evaluation_results.json`
- `evaluation_report.md`

Compare against `reports/vision_no_ocr/` after running:

```bash
python evaluate.py --mode vision
```
