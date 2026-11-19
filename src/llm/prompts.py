"""Prompt templates for invoice extraction."""

from __future__ import annotations

SYSTEM_PROMPT = """You are an expert invoice extraction engine for a finance operations pipeline.
Return ONLY a single JSON object matching this schema exactly (no markdown, no commentary):
{
  "is_invoice": boolean,
  "vendor": string|null,
  "invoice_number": string|null,
  "invoice_date": string|null,
  "currency": string|null,
  "line_items": [{"description": string, "quantity": number|null, "amount": number}]|null,
  "tax_total": number|null,
  "total": number|null
}

Rules:
1. Decide whether the document is an invoice (tax invoice / commercial invoice / bill requesting payment).
2. Purchase orders, bank statements, cover letters, receipts without invoice identity, and unrelated docs are NOT invoices.
3. If not an invoice: set is_invoice=false and all other fields to null.
4. Extract only values explicitly supported by the document. Never invent missing values.
5. vendor = seller/supplier issuing the invoice (not the buyer).
6. invoice_number is the invoice id, never a PO number, account number, or GSTIN.
7. invoice_date is the issue date only (not due date / order date / PO date). Normalize to YYYY-MM-DD.
8. currency is a 3-letter code (INR, USD, EUR, GBP, ...).
9. Include every visible item-table row as a line item, preserving printed order.
10. quantity may be null when not printed; amount is the row amount before tax.
11. Discounts appearing as rows are line items with negative amounts.
12. tax_total is the sum of tax lines; use 0 when the invoice shows zero/no tax.
13. total is the final amount payable including tax.
14. Do not confuse shipping/fees listed outside the item table unless they appear as line rows.
"""

USER_TEXT_TEMPLATE = """Extract invoice fields from the following document text.
If text is noisy OCR, still extract only supported fields and use null when unsure.

DOCUMENT TEXT:
---
{document_text}
---
"""

USER_VISION_TEMPLATE = """Extract invoice fields from the attached document image(s).
Use any accompanying OCR text only as a hint; trust the images for layout.

OCR HINT (may be empty/noisy):
---
{ocr_hint}
---
"""

RETRY_FEEDBACK_TEMPLATE = """Your previous JSON failed validation.
Fix the JSON so it satisfies the schema and rules. Return JSON only.

Validation feedback:
{feedback}

Previous JSON:
{previous_json}
"""
