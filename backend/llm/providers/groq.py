"""
DataWise AI — Fallback 1 LLM Provider: Groq
Ultra-low-latency Llama-3.3-70b inference via Groq Cloud API.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional
import httpx
from loguru import logger

try:
    from llm.base import LLMProvider, LLMResponse
    from llm.circuit_breaker import circuit_registry
    from llm.quota_manager import quota_manager
except ImportError:
    from backend.llm.base import LLMProvider, LLMResponse
    from backend.llm.circuit_breaker import circuit_registry
    from backend.llm.quota_manager import quota_manager


class GroqProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: float = 20.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("GROQ_API_KEY", "")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.circuit_breaker = circuit_registry.get_breaker("groq")

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
                content="[Groq Fallback: GROQ_API_KEY not configured]",
                model_name=self.model,
                provider="groq",
                finish_reason="stop",
            )

        if not self.circuit_breaker.allow_request():
            logger.warning("[GroqProvider] Circuit is OPEN. Fast failing to Cloudflare fallback.")
            return LLMResponse(
                content="[Circuit Breaker OPEN for Groq]",
                model_name=self.model,
                provider="groq",
                finish_reason="error",
                error="Circuit Breaker OPEN",
            )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                elapsed = time.perf_counter() - start_time

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens")

                    self.circuit_breaker.record_success()
                    quota_manager.record_call(
                        provider_name="groq",
                        duration_seconds=elapsed,
                        tokens_used=tokens,
                    )

                    return LLMResponse(
                        content=content,
                        model_name=self.model,
                        provider="groq",
                        finish_reason="stop",
                        tokens_used=tokens,
                    )
                else:
                    is_429 = resp.status_code == 429
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    self.circuit_breaker.record_failure(err_msg)
                    quota_manager.record_call(
                        provider_name="groq",
                        duration_seconds=elapsed,
                        is_error=True,
                        is_429=is_429,
                        error_message=err_msg,
                    )
                    return LLMResponse(
                        content=f"[Groq Error: {err_msg}]",
                        model_name=self.model,
                        provider="groq",
                        finish_reason="error",
                        error=err_msg,
                    )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            err_msg = str(exc)
            self.circuit_breaker.record_failure(err_msg)
            quota_manager.record_call(
                provider_name="groq",
                duration_seconds=elapsed,
                is_error=True,
                error_message=err_msg,
            )
            logger.warning(f"[GroqProvider] Exception: {err_msg}")
            return LLMResponse(
                content=f"[Groq Error: {err_msg}]",
                model_name=self.model,
                provider="groq",
                finish_reason="error",
                error=err_msg,
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
