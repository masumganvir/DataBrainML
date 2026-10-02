"""
DataWise AI — Central LLM Module
"""

from .base import LLMProvider, LLMResponse
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider
from .model_registry import model_registry, ModelRegistry
from .fallback import FallbackExecutor
from .schemas import TaskType, ProviderType, ModelDescriptor, LLMGenerationRequest
from .router import LLMRouter, llm_router, TaskComplexity

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "GeminiProvider",
    "OllamaProvider",
    "ModelRegistry",
    "model_registry",
    "FallbackExecutor",
    "TaskType",
    "ProviderType",
    "ModelDescriptor",
    "LLMGenerationRequest",
    "LLMRouter",
    "llm_router",
    "TaskComplexity",
]
