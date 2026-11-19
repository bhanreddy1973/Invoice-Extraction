# Dataset Inventory (Phase 0)

**Source:** Es Magico sample pack downloaded from the assignment Google Drive folder  
`https://drive.google.com/drive/folders/1ACUAIhkqudad9WYQyTwgG3XxrgIlsFKz`  
**Local mirror:** `data/raw_download/`  
**Inspection date:** 2026-11-19  
**Method:** File listing + PyMuPDF text extraction + Pillow image metadata. Values below are observed, not assumed.

Also present in the pack:

| File | Role |
|---|---|
| `README.md` | Pack conventions and labelling rules |
| `schema.json` | Authoritative JSON Schema for extractor output |
| `labelled/` | 10 documents + matching ground-truth JSON |
| `unlabelled/` | 10 documents, no answers |

---

## Summary counts (observed)

| Category | Count | IDs |
|---|---:|---|
| Total documents | 20 | L01–L10, U01–U10 |
| Labelled | 10 | L01–L10 |
| Unlabelled | 10 | U01–U10 |
| Digital PDF with selectable text | 15 | L01, L03–L08, U01, U03–U04, U06–U10 |
| Scanned / image-only PDF (0 selectable alnum chars) | 3 | L09, L10, U05 |
| Photograph / JPG | 2 | L02, U02 |
| Labelled invoices (`is_invoice: true`) | 9 | L01–L07, L09–L10 |
| Labelled non-invoice | 1 | L08 (Purchase Order) |
| Multi-page | 1 | L04 (2 pages) |

Unlabelled non-invoice candidates from **text preview only** (not ground truth):

- `U06.pdf` — bank account statement (`Harbor Trust Bank`)
- `U10.pdf` — cover letter / job application (`Rhea Menon`)

These are hypotheses for bad-input handling; final labels are held by Es Magico.

---

## Document inventory

| Document | Format | Pages | Category (observed) | Label available | GT `is_invoice` | Notes |
|---|---|---:|---|---|---|---|
| L01 | PDF | 1 | Digital invoice | Yes | true | ReportLab; GBP; 4 line items |
| L02 | JPG | 1 | Photographed invoice | Yes | true | 1500×2070 RGB; vendor Shree Ganesh Stationers |
| L03 | PDF | 1 | Digital invoice | Yes | true | INR tax invoice |
| L04 | PDF | 2 | Digital invoice | Yes | true | Large table (24 line items); freight/charges as rows |
| L05 | PDF | 1 | Digital invoice | Yes | true | INR; 10 line items |
| L06 | PDF | 1 | Digital invoice | Yes | true | Nullable quantities in GT; professional services |
| L07 | PDF | 1 | Digital invoice | Yes | true | USD; negative discount line item |
| L08 | PDF | 1 | Digital **non-invoice** (PO) | Yes | false | Purchase Order; all other fields null |
| L09 | PDF | 1 | Scanned invoice | Yes | true | 0 embedded text chars; Coastal Fresh Seafoods |
| L10 | PDF | 1 | Scanned invoice | Yes | true | 0 embedded text chars; Metro Auto Parts |
| U01 | PDF | 1 | Digital (appears invoice) | No | — | Blue Lotus Hospitality |
| U02 | JPG | 1 | Photograph | No | — | 1050×1449 RGB |
| U03 | PDF | 1 | Digital (appears invoice) | No | — | Quickserve IT Rentals |
| U04 | PDF | 1 | Digital (appears invoice) | No | — | Bluefin Cloud Services |
| U05 | PDF | 1 | Scanned / image PDF | No | — | 0 embedded text chars |
| U06 | PDF | 1 | Digital **non-invoice candidate** | No | — | Bank statement preview |
| U07 | PDF | 1 | Digital (appears invoice, DE) | No | — | German `RECHNUNG` |
| U08 | PDF | 1 | Digital (appears invoice, NL) | No | — | Sakura Tea Traders B.V. |
| U09 | PDF | 1 | Digital (appears invoice) | No | — | Greenleaf Catering Co |
| U10 | PDF | 1 | Digital **non-invoice candidate** | No | — | Cover letter preview |

---

## Ground-truth mapping

| Source document | Ground-truth file | Mapping rule |
|---|---|---|
| `labelled/L0N.pdf` or `labelled/L0N.jpg` | `labelled/L0N.json` | Same stem |
| `unlabelled/U0N.*` | _(none)_ | No GT provided |

---

## Schema notes from pack (authoritative vs master prompt)

Observed in `schema.json` / pack README — these override informal assumptions in the master prompt where they differ:

1. `quantity` may be `number` **or** `null` (e.g. L06 retainer, L07 discount).
2. `currency` must match `^[A-Z]{3}$` when present.
3. `invoice_date` must match `YYYY-MM-DD` when present.
4. `additionalProperties: false` on the root and line items.
5. Non-invoice ⇒ every field except `is_invoice` is JSON `null`.
6. Discount rows are line items with **negative** `amount` (L07).
7. Charges that appear in the item table are line items (L04 freight/setup).
8. `tax_total` is `0` when tax is zero/absent (pack rule); do not confuse with missing/`null` on non-invoices.
9. Amounts are plain JSON numbers (no thousands separators).

---

## Financial consistency spot-check (GT only)

Baseline: `sum(line_item.amount) + tax_total == total` (exact Decimal equality on labelled GT).

| Doc | Line sum | Tax | Expected total | GT total | Match |
|---|---:|---:|---:|---:|---|
| L01 | 569.5 | 113.9 | 683.4 | 683.4 | Yes |
| L07 | 4050.0 | 334.13 | 4384.13 | 4384.13 | Yes |

Full GT suite will be checked by the financial validator during implementation.

---

## Dataset challenges for the pipeline

1. **Mixed modalities:** digital text PDF, scanned PDF, JPG photo.
2. **Non-invoices:** at least one labelled PO (L08); likely bank statement + cover letter in unlabelled.
3. **Nullable / fractional quantities:** L06 (`null`), L09 (`12.5`, `9.5`).
4. **Negative amounts:** L07 discount.
5. **Large line tables:** L04 (24 items, 2 pages).
6. **Multi-currency / locales:** GBP, INR, USD; unlabelled DE/NL date formats.
7. **PO vs invoice confusion risk:** L08 has PO number/date — must not be treated as invoice fields.

---

## Missing / blocked items before claiming full evaluation

| Item | Status |
|---|---|
| 20 sample documents | Available locally under `data/raw_download/` |
| 10 ground-truth JSON files | Available |
| Pack `schema.json` | Available |
| LLM API credentials | **Not yet configured in this workspace** |
| Tesseract OCR binary | **Not yet verified on this machine** |

Real evaluation numbers, cost figures, and all-20 outputs require a configured LLM (and OCR for scan/photo routes).
