"""
DataWise AI — Anthropic LLM Provider Implementation
"""

import os
from typing import Optional
from backend.llm.provider import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="[Deterministic Fallback: ANTHROPIC_API_KEY not configured]",
                model_name=self.model,
                provider="anthropic",
            )
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_instruction:
                kwargs["system"] = system_instruction
            resp = client.messages.create(**kwargs)
            text = resp.content[0].text if resp.content else ""
            return LLMResponse(
                content=text,
                model_name=self.model,
                provider="anthropic",
            )
        except Exception as e:
            return LLMResponse(
                content=f"[Anthropic Error: {str(e)}]",
                model_name=self.model,
                provider="anthropic",
                finish_reason="error",
            )

    async def agenerate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> LLMResponse:
        return self.generate(prompt, system_instruction, temperature, max_tokens)
