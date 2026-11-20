# Cost Analysis

- Provider: NVIDIA Integrate API (`https://integrate.api.nvidia.com/v1`)
- Text model: `nvidia/nemotron-3.5-bolt-e4b`
- Vision model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- Pricing source: NVIDIA Integrate API free-tier / catalog entitlement
- Pricing effective date: 2026-11-19

## Observed usage (from batch run)

- Documents processed: 20
- Total input tokens (reported): 39259
- Total output tokens (reported): 17060
- Total API cost (USD): 0.000000
- Average cost per document (USD): 0.000000
- Average latency (s): 15.38

## Methodology

Cost = (input_tokens / 1e6 * input_price) + (output_tokens / 1e6 * output_price).
Configured free-tier prices are $0.00 / 1M tokens for the selected NVIDIA catalog models.
Local Tesseract OCR compute is excluded from API cost.
Token counts are taken from provider usage when returned; missing values are recorded as 0 and flagged.
