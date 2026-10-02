"""
DataWise AI — LLM Model Registry
Tracks available models, token boundaries, and provider configurations.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from .schemas import ModelDescriptor, ProviderType


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelDescriptor] = {}
        self._register_default_models()

    def _register_default_models(self) -> None:
        self.register(
            ModelDescriptor(
                model_name="gemini-2.0-flash",
                provider=ProviderType.GEMINI,
                context_window=1048576,
                supports_system_prompt=True,
                supports_json_schema=True,
                is_local=False,
                description="Fast and versatile multimodal model with strong reasoning.",
            )
        )
        self.register(
            ModelDescriptor(
                model_name="gemini-1.5-pro",
                provider=ProviderType.GEMINI,
                context_window=2097152,
                supports_system_prompt=True,
                supports_json_schema=True,
                is_local=False,
                description="Deep reasoning model with massive context window.",
            )
        )
        self.register(
            ModelDescriptor(
                model_name="qwen2.5:7b",
                provider=ProviderType.OLLAMA,
                context_window=32768,
                supports_system_prompt=True,
                supports_json_schema=True,
                is_local=True,
                description="High quality open-weight model for local and privacy-sensitive inference.",
            )
        )
        self.register(
            ModelDescriptor(
                model_name="qwen2.5-coder:7b",
                provider=ProviderType.OLLAMA,
                context_window=32768,
                supports_system_prompt=True,
                supports_json_schema=True,
                is_local=True,
                description="Specialized code generation and execution reasoning model.",
            )
        )

    def register(self, descriptor: ModelDescriptor) -> None:
        self._models[descriptor.model_name] = descriptor

    def get(self, model_name: str) -> Optional[ModelDescriptor]:
        return self._models.get(model_name)

    def list_models(self, provider: Optional[ProviderType] = None) -> List[ModelDescriptor]:
        if provider:
            return [m for m in self._models.values() if m.provider == provider]
        return list(self._models.values())


model_registry = ModelRegistry()
