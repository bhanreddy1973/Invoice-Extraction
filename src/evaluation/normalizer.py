"""Normalize predicted and ground-truth values for comparison."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_currency(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip().upper()


def normalize_number(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    text = str(value).strip()
    text = text.replace(",", "")
    text = re.sub(r"[^\d.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return text
    return text


def numbers_equal(a: Any, b: Any, *, tol: Decimal = Decimal("0.01")) -> bool:
    na = normalize_number(a)
    nb = normalize_number(b)
    if na is None and nb is None:
        return True
    if na is None or nb is None:
        return False
    return (na - nb).copy_abs() <= tol
