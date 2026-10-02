"""
DataWise AI — Tests for LLM Provider Abstraction & Model Routing
"""

import pytest
from llm.base import LLMProvider, LLMResponse
from llm.providers.gemini import GeminiProvider
from llm.ollama_provider import OllamaProvider
from llm.model_registry import model_registry, ModelDescriptor, ProviderType
from llm.fallback import FallbackExecutor
from llm.schemas import TaskType
from llm.router import LLMRouter, llm_router


class MockSuccessProvider(LLMProvider):
    def __init__(self, name="mock_primary"):
        self.name = name

    def generate(self, prompt, system_instruction=None, temperature=0.2, max_tokens=1500):
        return LLMResponse(
            content=f"Response from {self.name}",
            model_name=self.name,
            provider="mock",
            finish_reason="stop",
        )

    async def agenerate(self, prompt, system_instruction=None, temperature=0.2, max_tokens=1500):
        return self.generate(prompt, system_instruction, temperature, max_tokens)


class MockFailingProvider(LLMProvider):
    def __init__(self, name="mock_failing"):
        self.name = name

    def generate(self, prompt, system_instruction=None, temperature=0.2, max_tokens=1500):
        raise RuntimeError(f"Connection failure in {self.name}")

    async def agenerate(self, prompt, system_instruction=None, temperature=0.2, max_tokens=1500):
        raise RuntimeError(f"Async failure in {self.name}")


def test_model_registry():
    gemini_desc = model_registry.get("gemini-2.0-flash")
    assert gemini_desc is not None
    assert gemini_desc.provider == ProviderType.GEMINI

    ollama_desc = model_registry.get("qwen2.5:7b")
    assert ollama_desc is not None
    assert ollama_desc.is_local is True


def test_fallback_executor_success_primary():
    primary = MockSuccessProvider("primary")
    fallback = MockSuccessProvider("fallback")

    res = FallbackExecutor.execute_with_fallback([primary, fallback], "Hello")
    assert res.content == "Response from primary"
    assert res.is_fallback is False


def test_fallback_executor_activates_fallback_on_error():
    failing = MockFailingProvider("failing_primary")
    backup = MockSuccessProvider("backup")

    res = FallbackExecutor.execute_with_fallback([failing, backup], "Hello")
    assert res.content == "Response from backup"
    assert res.is_fallback is True


def test_fallback_executor_all_fail_gracefully():
    failing1 = MockFailingProvider("failing1")
    failing2 = MockFailingProvider("failing2")

    res = FallbackExecutor.execute_with_fallback([failing1, failing2], "Hello")
    assert "Deterministic Fallback" in res.content
    assert res.finish_reason == "fallback"


def test_router_routing_chains():
    from llm.providers.groq import GroqProvider
    from llm.providers.cloudflare import CloudflareProvider

    router = LLMRouter()

    # Spec Sections 2 & 3: Gemini (Primary) -> Groq (Fallback 1) -> Cloudflare (Fallback 2)
    chain = router.get_provider_chain("model_selection")
    assert any(isinstance(p, GeminiProvider) for p in chain)
    assert any(isinstance(p, GroqProvider) for p in chain)
    assert any(isinstance(p, CloudflareProvider) for p in chain)
    # Primary is Gemini
    assert isinstance(chain[0], GeminiProvider)
    # First fallback is Groq
    assert isinstance(chain[1], GroqProvider)
    # Second fallback is Cloudflare
    assert isinstance(chain[2], CloudflareProvider)


def test_gemini_provider_unconfigured_fallback():
    provider = GeminiProvider(api_key="")
    res = provider.generate("Test prompt")
    assert "GEMINI_API_KEY not configured" in res.content
    assert res.provider == "gemini"


def test_ollama_provider_offline_handling():
    provider = OllamaProvider(base_url="http://127.0.0.1:99999", timeout=0.1)
    res = provider.generate("Test prompt")
    assert "Offline" in res.content or "error" in res.finish_reason
