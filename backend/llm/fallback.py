"""
DataWise AI — LLM Fallback Policy & Resilient Invocation Engine
Handles primary provider failures, timeouts, and quota exhaustion by falling back
to local or alternate models (e.g. Gemini -> Ollama, or Local Coder -> Gemini).
"""

from __future__ import annotations

from typing import List, Optional
from loguru import logger

from .base import LLMProvider, LLMResponse


class FallbackExecutor:
    """Executes requests with an ordered sequence of providers until one succeeds."""

    @staticmethod
    def execute_with_fallback(
        providers: List[LLMProvider],
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        errors = []
        for idx, provider in enumerate(providers):
            try:
                response = provider.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                # If finished successfully and not a canned error string
                if response.finish_reason != "error" and not response.content.startswith("[Gemini Error"):
                    if idx > 0:
                        response.is_fallback = True
                        logger.info(
                            f"[FallbackExecutor] Succeeded using fallback provider: {response.provider} ({response.model_name})"
                        )
                    return response
                else:
                    errors.append(f"{provider.__class__.__name__}: {response.content}")
            except Exception as exc:
                errors.append(f"{provider.__class__.__name__} exception: {str(exc)}")
                logger.warning(f"[FallbackExecutor] Provider {provider.__class__.__name__} failed: {exc}")

        # If all providers fail, return a structured deterministic fallback response
        error_summary = " | ".join(errors)
        logger.error(f"[FallbackExecutor] All providers failed: {error_summary}")
        return LLMResponse(
            content=f"[Deterministic Fallback: LLM providers unavailable ({error_summary})]",
            model_name="deterministic_rule_based",
            provider="system_fallback",
            finish_reason="fallback",
            error=error_summary,
            is_fallback=True,
        )

    @staticmethod
    async def aexecute_with_fallback(
        providers: List[LLMProvider],
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        errors = []
        for idx, provider in enumerate(providers):
            try:
                response = await provider.agenerate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if response.finish_reason != "error" and not response.content.startswith("[Gemini Error"):
                    if idx > 0:
                        response.is_fallback = True
                        logger.info(
                            f"[FallbackExecutor] Succeeded using fallback provider: {response.provider} ({response.model_name})"
                        )
                    return response
                else:
                    errors.append(f"{provider.__class__.__name__}: {response.content}")
            except Exception as exc:
                errors.append(f"{provider.__class__.__name__} exception: {str(exc)}")
                logger.warning(f"[FallbackExecutor] Provider {provider.__class__.__name__} failed: {exc}")

        error_summary = " | ".join(errors)
        logger.error(f"[FallbackExecutor] All async providers failed: {error_summary}")
        return LLMResponse(
            content=f"[Deterministic Fallback: LLM providers unavailable ({error_summary})]",
            model_name="deterministic_rule_based",
            provider="system_fallback",
            finish_reason="fallback",
            error=error_summary,
            is_fallback=True,
        )
