"""
DataWise AI — Fallback 2 LLM Provider: Cloudflare Workers AI
Serverless edge LLM inference via Cloudflare Workers AI.
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


class CloudflareProvider(LLMProvider):
    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 25.0,
    ):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        self.api_token = (
            api_token
            if api_token is not None
            else (os.getenv("CLOUDFLARE_API_TOKEN", "") or os.getenv("CLAUDEFLARE_AI_WORKER_API_KEY", ""))
        )
        self.model = model or os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct")
        self.timeout = timeout
        self.circuit_breaker = circuit_registry.get_breaker("cloudflare")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        if not self.account_id or not self.api_token:
            return LLMResponse(
                content="[Cloudflare Fallback: CLOUDFLARE credentials not configured]",
                model_name=self.model,
                provider="cloudflare",
                finish_reason="stop",
            )

        if not self.circuit_breaker.allow_request():
            logger.warning("[CloudflareProvider] Circuit is OPEN.")
            return LLMResponse(
                content="[Circuit Breaker OPEN for Cloudflare]",
                model_name=self.model,
                provider="cloudflare",
                finish_reason="error",
                error="Circuit Breaker OPEN",
            )

        endpoint = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(endpoint, json=payload, headers=headers)
                elapsed = time.perf_counter() - start_time

                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    content = result.get("response", "")

                    self.circuit_breaker.record_success()
                    quota_manager.record_call(
                        provider_name="cloudflare",
                        duration_seconds=elapsed,
                    )

                    return LLMResponse(
                        content=content,
                        model_name=self.model,
                        provider="cloudflare",
                        finish_reason="stop",
                    )
                else:
                    is_429 = resp.status_code == 429
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    self.circuit_breaker.record_failure(err_msg)
                    quota_manager.record_call(
                        provider_name="cloudflare",
                        duration_seconds=elapsed,
                        is_error=True,
                        is_429=is_429,
                        error_message=err_msg,
                    )
                    return LLMResponse(
                        content=f"[Cloudflare Error: {err_msg}]",
                        model_name=self.model,
                        provider="cloudflare",
                        finish_reason="error",
                        error=err_msg,
                    )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            err_msg = str(exc)
            self.circuit_breaker.record_failure(err_msg)
            quota_manager.record_call(
                provider_name="cloudflare",
                duration_seconds=elapsed,
                is_error=True,
                error_message=err_msg,
            )
            logger.warning(f"[CloudflareProvider] Exception: {err_msg}")
            return LLMResponse(
                content=f"[Cloudflare Error: {err_msg}]",
                model_name=self.model,
                provider="cloudflare",
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
