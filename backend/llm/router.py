"""
DataWise AI — Intelligent Online LLM Model Router (Sections 2 & 3)
Orchestrates multi-tier enterprise AI resilience:
  Primary:   Google Gemini
  Fallback 1: Groq (Llama-3.3-70b)
  Fallback 2: Cloudflare Workers AI (Llama-3.1-8b)
  Local:     Ollama (Qwen2.5 / Qwen3)
  Final:     Deterministic rule-based execution (Never fails the data science pipeline!)
Features circuit breaking, rate-limit quota tracking, semantic Redis caching, and exponential retry.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, List, Optional
from loguru import logger

try:
    from llm.base import LLMProvider, LLMResponse
    from llm.providers.gemini import GeminiProvider
    from llm.providers.groq import GroqProvider
    from llm.providers.cloudflare import CloudflareProvider
    from llm.ollama_provider import OllamaProvider
    from llm.fallback import FallbackExecutor
    from llm.cache import llm_cache
    from llm.schemas import TaskType
except ImportError:
    from backend.llm.base import LLMProvider, LLMResponse
    from backend.llm.providers.gemini import GeminiProvider
    from backend.llm.providers.groq import GroqProvider
    from backend.llm.providers.cloudflare import CloudflareProvider
    from backend.llm.ollama_provider import OllamaProvider
    from backend.llm.fallback import FallbackExecutor
    from backend.llm.cache import llm_cache
    from backend.llm.schemas import TaskType


class TaskComplexity(str, Enum):
    FAST = "fast"
    STRONG = "strong"


class LLMRouter:
    def __init__(self):
        # 1. Primary & Fallback Providers
        self.gemini_provider = GeminiProvider()
        self.groq_provider = GroqProvider()
        self.cloudflare_provider = CloudflareProvider()

        # 2. Local Provider
        self.ollama_primary = OllamaProvider(
            model=os.getenv("OLLAMA_PRIMARY_MODEL", "qwen2.5:7b")
        )
        self.ollama_coder = OllamaProvider(
            model=os.getenv("OLLAMA_CODING_MODEL", "qwen2.5-coder:7b")
        )

        self._providers: Dict[str, LLMProvider] = {
            "gemini": self.gemini_provider,
            "groq": self.groq_provider,
            "cloudflare": self.cloudflare_provider,
            "ollama": self.ollama_primary,
        }

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        name = (provider_name or os.getenv("LLM_PROVIDER", "gemini")).lower()
        if name not in self._providers:
            if name == "openai":
                from backend.llm.openai import OpenAIProvider
                self._providers["openai"] = OpenAIProvider()
            elif name == "anthropic":
                from backend.llm.anthropic import AnthropicProvider
                self._providers["anthropic"] = AnthropicProvider()
        return self._providers.get(name, self.gemini_provider)

    def get_provider_chain(self, task: str = "general") -> List[LLMProvider]:
        """
        Primary: Gemini
        Fallback 1: Groq
        Fallback 2: Cloudflare Workers AI
        Optional local fallback: Ollama
        """
        chain = [self.gemini_provider, self.groq_provider, self.cloudflare_provider]
        if self.ollama_primary.is_available():
            chain.append(self.ollama_primary)
        return chain

    def generate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """
        Unified router generation method specified in Master Spec Section 2:
        router.generate(task="model_selection", context=context)
        """
        actual_prompt = prompt or ""
        if context and not prompt:
            # Format context dictionary into readable text prompt
            import json
            actual_prompt = (
                f"TASK: {task}\n"
                f"CONTEXT DATA (Computed deterministically by Python):\n"
                f"{json.dumps(context, indent=2, default=str)}"
            )

        # 1. Check Cache
        cache_key = llm_cache.generate_cache_key(
            provider="router",
            model="dynamic",
            task=task,
            prompt=actual_prompt,
            system_instruction=system_instruction,
            user_id=user_id,
        )
        cached = llm_cache.get(cache_key)
        if cached:
            return cached

        # 2. Execute with multi-tier fallback (Gemini -> Groq -> Cloudflare -> Ollama)
        chain = self.get_provider_chain(task)
        response = FallbackExecutor.execute_with_fallback(
            providers=chain,
            prompt=actual_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 3. Store in Cache if valid
        if response.finish_reason != "error":
            llm_cache.set(cache_key, response)

        return response

    async def agenerate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """Asynchronous unified router generation."""
        actual_prompt = prompt or ""
        if context and not prompt:
            import json
            actual_prompt = (
                f"TASK: {task}\n"
                f"CONTEXT DATA (Computed deterministically by Python):\n"
                f"{json.dumps(context, indent=2, default=str)}"
            )

        # 1. Check Cache
        cache_key = llm_cache.generate_cache_key(
            provider="router",
            model="dynamic",
            task=task,
            prompt=actual_prompt,
            system_instruction=system_instruction,
            user_id=user_id,
        )
        cached = llm_cache.get(cache_key)
        if cached:
            return cached

        # 2. Asynchronous execution
        chain = self.get_provider_chain(task)
        response = await FallbackExecutor.aexecute_with_fallback(
            providers=chain,
            prompt=actual_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if response.finish_reason != "error":
            llm_cache.set(cache_key, response)

        return response

    # Backward compatibility with TaskType enum & route_and_generate
    def route(
        self,
        task_type: Any,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        task_name = task_type.value if hasattr(task_type, "value") else str(task_type)
        return self.generate(
            task=task_name,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def route_and_generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        complexity: TaskComplexity = TaskComplexity.FAST,
        temperature: float = 0.2,
    ) -> LLMResponse:
        task = "complex_reasoning" if complexity == TaskComplexity.STRONG else "fast_simple"
        max_tokens = 2500 if complexity == TaskComplexity.STRONG else 800
        return self.generate(
            task=task,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
        )


llm_router = LLMRouter()
