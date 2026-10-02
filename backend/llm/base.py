"""
DataWise AI — LLM Provider Base Interface & Standard Contracts
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    model_name: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = "stop"
    raw_response: Optional[Dict[str, Any]] = None
    is_fallback: bool = False
    error: Optional[str] = None


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        """Synchronously generate text completion."""
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        """Asynchronously generate text completion."""
        pass
