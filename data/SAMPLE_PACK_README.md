# Es Magico | AI Intern Assignment | Sample Pack

Sample documents for the **Invoice Extraction Pipeline** assignment. Everything here is synthetic: all companies, people, invoice numbers and amounts are fictional.

## What is in this folder

```
README.md          this file
schema.json        JSON Schema for the output your extractor must return
labelled/          10 documents (L01 ... L10), each with a ground-truth file (L01.json ...)
unlabelled/        10 documents (U01 ... U10), no answers provided
```

Documents are PDFs or JPG images. Some are clean digital PDFs, some are scans or phone photos, and some are not invoices.

## How to use it

- **labelled/** is what you evaluate on. Your eval harness compares your output for `L01.pdf` against `L01.json`.
- **unlabelled/** is where you just run your pipeline and include the outputs in your submission. We hold the answers.
- Treat the labelled set as your only test data. If you tune prompts or rules against it, say so in your report.

## Output schema

Your extractor returns one JSON object per document (see `schema.json`):

| Field | Type | Meaning |
|---|---|---|
| `is_invoice` | boolean | `true` only if the document is an invoice |
| `vendor` | string or null | The seller who issued the invoice |
| `invoice_number` | string or null | The invoice number |
| `invoice_date` | string or null | The invoice (issue) date, as `YYYY-MM-DD` |
| `currency` | string or null | ISO 4217 code, for example `INR`, `USD`, `EUR`, `GBP` |
| `line_items` | array or null | One object per row in the invoice's item table (below) |
| `tax_total` | number or null | Total tax on the invoice |
| `total` | number or null | Final amount payable, including tax |

Each line item has `description` (string), `quantity` (number or null), `amount` (number).

## How the ground truth was labelled

These are the conventions behind the `.json` answers in `labelled/`:

1. `vendor` is the seller's name as printed at the top of the document.
2. `invoice_date` is the date the invoice was issued. It is not the due date, an order date or a PO date. Read day-first or month-first dates in the context of the document.
3. `line_items` follow the order printed. `description` is as printed. `quantity` is the number printed, or `null` if the row has no quantity. `amount` is the row total before tax.
4. Charges and discounts that appear as rows in the item table are line items too. A discount is a negative amount.
5. `tax_total` is the sum of all tax lines on the invoice. If the document shows zero tax or no tax at all, it is `0`.
6. `total` is the final amount payable.
7. Amounts are plain JSON numbers in the document's own currency, with no thousands separators or currency symbols.
8. For a document that is not an invoice, `is_invoice` is `false` and every other field is `null`.

Questions about the pack? Contact us using the details in the assignment brief.
