"""
DataWise AI — Ollama Local LLM Provider Implementation
Provides on-premise, zero-cost, privacy-preserving open-weight model inference (e.g. Qwen2.5/Qwen3, DeepSeek, Llama3).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import httpx
from loguru import logger

from .base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = (
            model
            or os.getenv("OLLAMA_PRIMARY_MODEL")
            or "qwen2.5:7b"
        )
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if local Ollama daemon is reachable and responding."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return LLMResponse(
                        content=data.get("response", ""),
                        model_name=self.model,
                        provider="ollama",
                        finish_reason="stop" if data.get("done") else "length",
                        tokens_used=data.get("eval_count"),
                        raw_response=data,
                    )
                else:
                    return LLMResponse(
                        content=f"[Ollama HTTP {resp.status_code}: {resp.text}]",
                        model_name=self.model,
                        provider="ollama",
                        finish_reason="error",
                        error=resp.text,
                    )
        except Exception as exc:
            logger.debug(f"[OllamaProvider] Ollama unavailable or connection error: {exc}")
            return LLMResponse(
                content=f"[Ollama Offline: {str(exc)}]",
                model_name=self.model,
                provider="ollama",
                finish_reason="error",
                error=str(exc),
            )

    async def agenerate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return LLMResponse(
                        content=data.get("response", ""),
                        model_name=self.model,
                        provider="ollama",
                        finish_reason="stop" if data.get("done") else "length",
                        tokens_used=data.get("eval_count"),
                        raw_response=data,
                    )
                else:
                    return LLMResponse(
                        content=f"[Ollama HTTP {resp.status_code}: {resp.text}]",
                        model_name=self.model,
                        provider="ollama",
                        finish_reason="error",
                        error=resp.text,
                    )
        except Exception as exc:
            logger.debug(f"[OllamaProvider] Ollama async connection error: {exc}")
            return LLMResponse(
                content=f"[Ollama Offline: {str(exc)}]",
                model_name=self.model,
                provider="ollama",
                finish_reason="error",
                error=str(exc),
            )
