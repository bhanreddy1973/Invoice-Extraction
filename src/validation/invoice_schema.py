"""Pydantic models matching the Es Magico pack schema.json."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float


class InvoiceExtraction(BaseModel):
    """Canonical external JSON schema for one document."""

    model_config = ConfigDict(extra="forbid")

    is_invoice: bool
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    currency: str | None = None
    line_items: list[LineItem] | None = None
    tax_total: float | None = None
    total: float | None = None

    @field_validator("invoice_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not DATE_RE.match(value):
            raise ValueError("invoice_date must be YYYY-MM-DD")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not CURRENCY_RE.match(normalized):
            raise ValueError("currency must be a 3-letter ISO code")
        return normalized

    @model_validator(mode="after")
    def non_invoice_nulls(self) -> InvoiceExtraction:
        if not self.is_invoice:
            for name in (
                "vendor",
                "invoice_number",
                "invoice_date",
                "currency",
                "line_items",
                "tax_total",
                "total",
            ):
                if getattr(self, name) is not None:
                    raise ValueError(f"{name} must be null when is_invoice is false")
        return self

    def to_public_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def non_invoice_result() -> InvoiceExtraction:
    return InvoiceExtraction(
        is_invoice=False,
        vendor=None,
        invoice_number=None,
        invoice_date=None,
        currency=None,
        line_items=None,
        tax_total=None,
        total=None,
    )
