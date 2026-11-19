from src.extraction.response_parser import extract_json_object
from src.exceptions import InvalidJSONError
import pytest


def test_parse_plain_json():
    payload = extract_json_object('{"is_invoice": false, "vendor": null}')
    assert payload["is_invoice"] is False


def test_parse_fenced_json():
    text = """```json
{"is_invoice": true, "vendor": "Acme"}
```"""
    payload = extract_json_object(text)
    assert payload["vendor"] == "Acme"


def test_invalid_json():
    with pytest.raises(InvalidJSONError):
        extract_json_object("not json at all")
