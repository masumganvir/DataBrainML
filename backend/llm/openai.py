"""
DataWise AI — OpenAI LLM Provider Implementation
"""

import os
from typing import Optional
from backend.llm.provider import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
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
                content="[Deterministic Fallback: OPENAI_API_KEY not configured]",
                model_name=self.model,
                provider="openai",
            )
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = resp.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model_name=self.model,
                provider="openai",
                tokens_used=resp.usage.total_tokens if resp.usage else None,
            )
        except Exception as e:
            return LLMResponse(
                content=f"[OpenAI Error: {str(e)}]",
                model_name=self.model,
                provider="openai",
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
