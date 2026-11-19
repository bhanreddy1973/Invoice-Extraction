"""Parse LLM text into JSON dicts with bounded repair."""

from __future__ import annotations

import json
import re
from typing import Any

from src.exceptions import InvalidJSONError

FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = FENCE_RE.search(cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        snippet = cleaned[start : end + 1]
        try:
            payload = json.loads(snippet)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError as exc:
            raise InvalidJSONError(f"Could not parse JSON object: {exc}") from exc

    raise InvalidJSONError("LLM response did not contain a JSON object")
