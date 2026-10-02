"""
DataWise AI — Google Gemini Primary LLM Provider
"""

from __future__ import annotations

import os
from typing import Optional
from loguru import logger

from .base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = (
            model
            or os.getenv("GEMINI_PRIMARY_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-2.0-flash"
        )

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        if not self.api_key:
            logger.debug("[GeminiProvider] GEMINI_API_KEY not configured. Returning deterministic fallback.")
            return LLMResponse(
                content="[Deterministic Fallback: GEMINI_API_KEY not configured]",
                model_name=self.model,
                provider="gemini",
                finish_reason="stop",
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
            text = response.text or ""
            return LLMResponse(
                content=text,
                model_name=self.model,
                provider="gemini",
                finish_reason="stop",
            )
        except Exception as exc:
            logger.warning(f"[GeminiProvider] Generation failed: {exc}")
            return LLMResponse(
                content=f"[Gemini Error: {str(exc)}]",
                model_name=self.model,
                provider="gemini",
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
        # In this Python process, we can run synchronous generate without blocking async event loop
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
