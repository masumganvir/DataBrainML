"""
DataWise AI — Primary LLM Provider: Google Gemini
"""

from __future__ import annotations

import os
import time
from typing import Optional
from loguru import logger

try:
    from llm.base import LLMProvider, LLMResponse
    from llm.circuit_breaker import circuit_registry
    from llm.quota_manager import quota_manager
except ImportError:
    from backend.llm.base import LLMProvider, LLMResponse
    from backend.llm.circuit_breaker import circuit_registry
    from backend.llm.quota_manager import quota_manager


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model = (
            model
            or os.getenv("GEMINI_PRIMARY_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-2.0-flash"
        )
        self.circuit_breaker = circuit_registry.get_breaker("gemini")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        if not self.api_key:
            return LLMResponse(
                content="[Deterministic Fallback: GEMINI_API_KEY not configured]",
                model_name=self.model,
                provider="gemini",
                finish_reason="stop",
            )

        if not self.circuit_breaker.allow_request():
            logger.warning("[GeminiProvider] Circuit is OPEN. Fast failing to next fallback.")
            return LLMResponse(
                content="[Circuit Breaker OPEN for Gemini]",
                model_name=self.model,
                provider="gemini",
                finish_reason="error",
                error="Circuit Breaker OPEN",
            )

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            full_prompt = (
                f"SYSTEM INSTRUCTION: {system_instruction}\n\nUSER PROMPT:\n{prompt}"
                if system_instruction
                else prompt
            )
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            elapsed = time.perf_counter() - start_time
            text = response.text or ""

            self.circuit_breaker.record_success()
            quota_manager.record_call(
                provider_name="gemini",
                duration_seconds=elapsed,
                tokens_used=getattr(response, "usage_metadata", None) and getattr(response.usage_metadata, "total_token_count", None),
            )

            return LLMResponse(
                content=text,
                model_name=self.model,
                provider="gemini",
                finish_reason="stop",
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            err_str = str(exc)
            is_429 = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()

            self.circuit_breaker.record_failure(err_str)
            quota_manager.record_call(
                provider_name="gemini",
                duration_seconds=elapsed,
                is_error=True,
                is_429=is_429,
                error_message=err_str,
            )
            logger.warning(f"[GeminiProvider] Error: {err_str}")

            return LLMResponse(
                content=f"[Gemini Error: {err_str}]",
                model_name=self.model,
                provider="gemini",
                finish_reason="error",
                error=err_str,
            )

    async def agenerate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate,
            prompt,
            system_instruction,
            temperature,
            max_tokens,
        )
