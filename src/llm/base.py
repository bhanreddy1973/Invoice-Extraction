"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMUsage:
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_seconds: float = 0.0
    request_count: int = 1
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage
    model: str


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete_text(self, *, system: str, user: str) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def complete_vision(self, *, system: str, user: str, images_png: list[bytes]) -> LLMResponse:
        raise NotImplementedError
