"""Estimate API cost from token usage and documented pricing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.llm.base import LLMUsage

# NVIDIA Integrate free/NIM catalog models used for this assignment are billed at $0
# through the free API key entitlement at the time of implementation.
# Source: NVIDIA API Catalog / Integrate free endpoints (verify in NGC pricing).
# Effective date recorded for auditability.
PRICING_SOURCE = "NVIDIA Integrate API free-tier / catalog entitlement"
PRICING_EFFECTIVE_DATE = date(2026, 11, 19)

# USD per 1M tokens. Free-tier models: 0.0. Update if switching to paid SKUs.
MODEL_PRICES_PER_MILLION: dict[str, dict[str, float]] = {
    "nvidia/nemotron-3.5-bolt-e4b": {"input": 0.0, "output": 0.0},
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {"input": 0.0, "output": 0.0},
    "nvidia/nemotron-3-ultra-550b-a55b": {"input": 0.0, "output": 0.0},
    "z-ai/glm-5.3-flash": {"input": 0.0, "output": 0.0},
    "moonshotai/kimi-k3.1-pro": {"input": 0.0, "output": 0.0},
}


@dataclass
class CostEstimate:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    pricing_source: str
    pricing_effective_date: str
    is_estimated: bool
    notes: str


class CostTracker:
    def estimate(self, usage: LLMUsage) -> CostEstimate:
        prices = MODEL_PRICES_PER_MILLION.get(usage.model, {"input": 0.0, "output": 0.0})
        inp = usage.input_tokens or 0
        out = usage.output_tokens or 0
        cost = (inp / 1_000_000) * prices["input"] + (out / 1_000_000) * prices["output"]
        missing = usage.input_tokens is None or usage.output_tokens is None
        notes = "Local OCR compute excluded from API cost."
        if missing:
            notes += " Provider did not return complete token usage; token fields treated as 0 where missing."
        if prices["input"] == 0.0 and prices["output"] == 0.0:
            notes += " Model priced at $0 under configured free-tier table."
        return CostEstimate(
            model=usage.model,
            input_tokens=inp,
            output_tokens=out,
            cost_usd=cost,
            pricing_source=PRICING_SOURCE,
            pricing_effective_date=PRICING_EFFECTIVE_DATE.isoformat(),
            is_estimated=missing or usage.model not in MODEL_PRICES_PER_MILLION,
            notes=notes,
        )

    def estimate_many(self, usages: list[LLMUsage]) -> CostEstimate:
        if not usages:
            return CostEstimate(
                model="",
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                pricing_source=PRICING_SOURCE,
                pricing_effective_date=PRICING_EFFECTIVE_DATE.isoformat(),
                is_estimated=False,
                notes="No API calls.",
            )
        parts = [self.estimate(u) for u in usages]
        model = usages[-1].model
        return CostEstimate(
            model=model,
            input_tokens=sum(p.input_tokens for p in parts),
            output_tokens=sum(p.output_tokens for p in parts),
            cost_usd=sum(p.cost_usd for p in parts),
            pricing_source=PRICING_SOURCE,
            pricing_effective_date=PRICING_EFFECTIVE_DATE.isoformat(),
            is_estimated=any(p.is_estimated for p in parts),
            notes=parts[-1].notes,
        )
