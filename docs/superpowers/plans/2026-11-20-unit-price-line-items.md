# Unit Price Line Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add public nullable `unit_price` on line items; when qty and unit_price exist, overwrite `amount = qty × unit_price` (2 dp); validate invoice totals with corrected amounts.

**Architecture:** Schema + Pydantic accept `unit_price`. Correction runs in `apply_unit_price_priority()` inside financial validation (mutates line amounts before sum check). Prompts teach the LLM the new field. Eval ignores `unit_price` vs GT.

**Tech Stack:** Pydantic, Decimal, existing pytest suite.

---

### Task 1: Schema + Pydantic + tests

**Files:**
- Modify: `data/schema.json`, `src/validation/invoice_schema.py`, `tests/test_schema.py`

- [x] Add `unit_price: number|null` to line items (required key, default null in Pydantic)
- [x] Tests for nullable unit_price and public dump including the field

### Task 2: Qty × unit_price priority + financial validation

**Files:**
- Modify: `src/validation/financial_validator.py`, `tests/test_financial_validation.py`
- Modify: `src/validation/__init__.py` if exporting helper

- [x] `apply_unit_price_priority(extraction) -> int` overwrites amounts when both qty and rate present
- [x] `validate_financials` applies priority first, then sum+tax≈total
- [x] Tests: wrong amount corrected to match; missing rate leaves amount alone

### Task 3: Prompts + eval ignore + README note

**Files:**
- Modify: `src/llm/prompts.py`, `src/evaluation/evaluator.py` (comment only if already ignoring), `README.md` output schema section

- [x] Prompt schema/rules for unit_price
- [x] Confirm `_line_items_match` ignores unit_price
- [x] Document extended line-item fields

### Task 4: Verify

- [x] `pytest -q` passes (31 passed)
