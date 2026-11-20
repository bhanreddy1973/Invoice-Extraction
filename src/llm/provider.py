"""NVIDIA Integrate API provider (OpenAI-compatible + vision)."""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from src.config import Settings, get_settings
from src.exceptions import LLMProviderError, LLMRateLimitError, LLMTimeoutError
from src.llm.base import BaseLLMProvider, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


class NVIDIAProvider(BaseLLMProvider):
    """Call NVIDIA-hosted models via the Integrate OpenAI-compatible endpoint."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.nvidia_api_key:
            raise LLMProviderError("NVIDIA_API_KEY is not set")
        self.client = OpenAI(
            base_url=self.settings.nvidia_base_url,
            api_key=self.settings.nvidia_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )

    def complete_text(self, *, system: str, user: str) -> LLMResponse:
        return self._chat(
            model=self.settings.nvidia_text_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            vision=False,
        )

    def complete_vision(self, *, system: str, user: str, images_png: list[bytes]) -> LLMResponse:
        content: list[dict[str, Any]] = [{"type": "text", "text": user}]
        for png in images_png:
            b64 = base64.b64encode(png).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )
        return self._chat(
            model=self.settings.nvidia_vision_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            vision=True,
        )

    def _chat(self, *, model: str, messages: list[dict[str, Any]], vision: bool) -> LLMResponse:
        extra_body: dict[str, Any] = {}
        if not vision and self.settings.enable_thinking:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}

        started = time.perf_counter()
        try:
            # Defaults aligned with NVIDIA Integrate examples for GLM Flash.
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5,
                top_p=1.0,
                max_tokens=4096,
                frequency_penalty=0,
                presence_penalty=0,
                seed=0,
                stream=False,
                extra_body=extra_body or None,
            )
        except RateLimitError as exc:
            raise LLMRateLimitError("NVIDIA API rate limit exceeded") from exc
        except APITimeoutError as exc:
            raise LLMTimeoutError("NVIDIA API request timed out") from exc
        except APIConnectionError as exc:
            raise LLMProviderError(f"NVIDIA API connection error: {exc}") from exc
        except APIStatusError as exc:
            raise LLMProviderError(f"NVIDIA API status error: {exc.status_code} {exc.message}") from exc
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"NVIDIA API call failed: {exc}") from exc

        latency = time.perf_counter() - started
        choice = completion.choices[0].message
        content = (choice.content or "").strip()
        # Some reasoning models put final answer after thinking; content field is preferred.
        usage_obj = completion.usage
        usage = LLMUsage(
            provider="nvidia",
            model=model,
            input_tokens=getattr(usage_obj, "prompt_tokens", None) if usage_obj else None,
            output_tokens=getattr(usage_obj, "completion_tokens", None) if usage_obj else None,
            total_tokens=getattr(usage_obj, "total_tokens", None) if usage_obj else None,
            latency_seconds=latency,
            raw={"id": getattr(completion, "id", None)},
        )
        if not content:
            raise LLMProviderError("NVIDIA API returned empty content")
        return LLMResponse(content=content, usage=usage, model=model)
