# Technical Walkthrough

Interview-oriented notes for each major component.

## PyMuPDF
Solves digital PDF text extraction and page rendering. We use text first because most labelled docs are ReportLab PDFs with selectable text; rendering is reserved for scans.

## OCR (Tesseract)
Solves scanned PDFs and photos when embedded text is absent. Preprocessing is conservative (denoise/threshold only when contrast is poor) to avoid destroying usable glyphs.

## Vision LLMs (Kimi on NVIDIA)
Used when OCR alphanumeric yield is below threshold. Images are sent as base64 `image_url` parts through the NVIDIA Integrate OpenAI-compatible API.

## Nemotron text model
Used for `pdf_text` and strong `ocr` routes. Prompt requires exact schema, nulls for missing values, and non-invoice nulling.

## Pydantic
Independent validation after the LLM. Pack schema rules include nullable quantity and non-invoice null constraints.

## Financial validation
`sum(line_amounts) + tax_total` compared to `total` with Decimal tolerance. Ambiguous mismatches are review-flagged.

## Evaluation
Field-level accuracy with normalization for whitespace/case, currency case, and numeric formatting. Line items are order-sensitive exact matches after normalization.
