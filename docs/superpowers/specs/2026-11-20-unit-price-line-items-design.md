# Design: Public `unit_price` + qty×rate priority

## Goal

Extract **unit price** per line item, prefer **amount = quantity × unit_price** when both are present, and validate that against row amount and invoice total so extractions stay financially consistent.

## Decision

- Add **public** `unit_price` on each line item (nullable number).
- When `quantity` and `unit_price` are both present → **overwrite `amount`** with `quantity × unit_price` (rounded to 2 decimal places).
- Keep pack-compatible fields; extend schema beyond original Es Magico pack (eval GT has no `unit_price` — comparison ignores it).

## Schema

Line item becomes:

```json
{
  "description": "string",
  "quantity": "number|null",
  "unit_price": "number|null",
  "amount": "number"
}
```

- `unit_price` required key; value may be `null` when not printed / not applicable.
- Non-invoice docs: all fields null as today.

## Correction priority (post-parse, pre-financial check)

For each line item:

1. If `quantity is not None` and `unit_price is not None`:
   - `computed = round(quantity * unit_price, 2)`
   - Set `amount = computed` (printed/LLM amount loses when both qty and rate exist).
2. Else keep extracted `amount`.

Invoice-level: after line correction, recompute expected total as `sum(amounts) + tax_total` and compare to `total` (existing tolerance). Optionally note line-level mismatches in financial reason / review metadata when LLM amount disagreed before overwrite.

## Validation

1. **Schema (Pydantic):** accept `unit_price: float | None`.
2. **Line check:** if qty + unit_price present, amount must equal qty×unit_price within tolerance (after correction this should always pass; if correction skipped because one is null, no line check).
3. **Invoice check (unchanged formula, corrected amounts):** `sum(amounts) + tax_total ≈ total`.

## Prompts

Update system prompt schema + rules:

- Extract `unit_price` when printed (rate / price each / unit cost).
- `null` when not shown (flat fees, lumpsum rows).
- Prefer consistency: if qty and unit price are clear, amount should match their product.

## Eval / GT

- Ground truth JSON has no `unit_price` → line-item match compares `description`, `quantity`, `amount` only; ignore `unit_price` for labelled accuracy.
- Schema validation of predictions requires `unit_price` key (nullable).

## Surfaces

- CLI / batch / FastAPI / Streamlit all use the same schema via `InvoicePipeline` — no separate UI logic beyond showing the new field in JSON/table.

## Out of scope

- Inferring unit_price from `amount / quantity` when rate is missing.
- Changing tax calculation rules.
- Backfilling labelled GT with unit prices.
