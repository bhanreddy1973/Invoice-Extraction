# Cost Analysis — Vision mode (no OCR)

- Provider: NVIDIA Integrate API (`https://integrate.api.nvidia.com/v1`)
- Text model (digital PDFs): `nvidia/nemotron-3-ultra-550b-a55b`
- Vision model (scans/photos): configured `NVIDIA_VISION_MODEL` (observed responses may report the served model id)
- Pricing source: NVIDIA Integrate free-tier / catalog entitlement
- Pricing effective date: 2026-11-19
- Local Tesseract cost: **excluded** (OCR disabled in this mode)

## Formula

```text
cost_usd =
  (input_tokens  / 1_000_000) * input_price_per_million
+ (output_tokens / 1_000_000) * output_price_per_million
```

Configured free-tier prices for selected models: **$0.00 / 1M tokens**.

## Observed usage (labelled eval, 10 docs)

| Metric | Value |
|---|---:|
| Total input tokens | 17,681 |
| Total output tokens | 12,200 |
| Avg input tokens / doc | 1,768.1 |
| Avg output tokens / doc | 1,220.0 |
| Total API cost (USD) | 0.000000 |
| Avg cost / doc (USD) | 0.000000 |
| Avg latency (s) | 12.23 |

Token counts are provider-reported usage fields from the chat completions API.
