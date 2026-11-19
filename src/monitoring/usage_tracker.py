"""Accumulate per-call LLM usage."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.llm.base import LLMUsage


@dataclass
class UsageTracker:
    records: list[LLMUsage] = field(default_factory=list)

    def record(self, usage: LLMUsage) -> None:
        self.records.append(usage)

    def total_input_tokens(self) -> int:
        return sum(u.input_tokens or 0 for u in self.records)

    def total_output_tokens(self) -> int:
        return sum(u.output_tokens or 0 for u in self.records)

    def total_latency(self) -> float:
        return sum(u.latency_seconds for u in self.records)

    def request_count(self) -> int:
        return sum(u.request_count for u in self.records)
