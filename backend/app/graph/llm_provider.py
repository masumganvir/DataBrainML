"""
DataWise AI — LLM Provider Abstraction & Model Routing

Wraps Google Gemini, OpenAI, and Anthropic APIs behind a unified interface:
  LLMProvider
  ├── GeminiProvider
  ├── OpenAIProvider
  └── AnthropicProvider

Supports Model Routing:
  - Fast task (simple explanations, classification of tool results, UI chat)
  - Capable task (complex reasoning, feature engineering, model strategy, report synthesis)
Falls back to MockProvider when no API keys are present in .env.
"""

from __future__ import annotations

import os
from typing import AsyncIterator, Dict, List, Literal, Optional

import httpx
from loguru import logger


# ------------------------------------------------------------------ #
#  Unified message type
# ------------------------------------------------------------------ #

class LLMMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


# ------------------------------------------------------------------ #
#  Base Provider
# ------------------------------------------------------------------ #

class BaseLLMProvider:
    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        raise NotImplementedError

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        raise NotImplementedError


# ------------------------------------------------------------------ #
#  Gemini Provider
# ------------------------------------------------------------------ #

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        try:
            import google.generativeai as genai  # type: ignore

            model_name = "gemini-1.5-pro" if task == "capable" else "gemini-1.5-flash"
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt or "You are DataWise AI, an expert autonomous data scientist.",
            )
            history = [{"role": "user" if m.role == "user" else "model", "parts": [m.content]} for m in messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(
                messages[-1].content,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Gemini completion failed: {exc}")
            return f"DataWise AI (Gemini fallback response for: {messages[-1].content[:60]}...)"

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        try:
            import google.generativeai as genai  # type: ignore

            model_name = "gemini-1.5-pro" if task == "capable" else "gemini-1.5-flash"
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt or "You are DataWise AI, an expert autonomous data scientist.",
            )
            history = [{"role": "user" if m.role == "user" else "model", "parts": [m.content]} for m in messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(
                messages[-1].content,
                stream=True,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Gemini stream failed: {exc}")
            yield f"DataWise AI (Gemini stream fallback for: {messages[-1].content[:60]}...)"


# ------------------------------------------------------------------ #
#  OpenAI Provider
# ------------------------------------------------------------------ #

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        try:
            from openai import AsyncOpenAI  # type: ignore

            model_name = "gpt-4o" if task == "capable" else "gpt-4o-mini"
            client = AsyncOpenAI(api_key=self.api_key)
            msg_list = []
            if system_prompt:
                msg_list.append({"role": "system", "content": system_prompt})
            msg_list.extend([m.to_dict() for m in messages])

            response = await client.chat.completions.create(
                model=model_name,
                messages=msg_list,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"OpenAI completion failed: {exc}")
            return f"DataWise AI (OpenAI fallback response for: {messages[-1].content[:60]}...)"

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI  # type: ignore

            model_name = "gpt-4o" if task == "capable" else "gpt-4o-mini"
            client = AsyncOpenAI(api_key=self.api_key)
            msg_list = []
            if system_prompt:
                msg_list.append({"role": "system", "content": system_prompt})
            msg_list.extend([m.to_dict() for m in messages])

            stream = await client.chat.completions.create(
                model=model_name,
                messages=msg_list,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"OpenAI stream failed: {exc}")
            yield f"DataWise AI (OpenAI stream fallback for: {messages[-1].content[:60]}...)"


# ------------------------------------------------------------------ #
#  Anthropic Provider
# ------------------------------------------------------------------ #

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        model_name = "claude-3-5-sonnet-20241022" if task == "capable" else "claude-3-5-haiku-20241022"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        anthropic_msgs = [{"role": ("user" if m.role == "user" else "assistant"), "content": m.content} for m in messages]
        payload = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_msgs,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content_blocks = data.get("content", [])
                    return "".join(b.get("text", "") for b in content_blocks)
                else:
                    logger.warning(f"Anthropic API returned status {res.status_code}: {res.text}")
                    return f"DataWise AI (Anthropic error {res.status_code})"
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Anthropic completion failed: {exc}")
            return f"DataWise AI (Anthropic fallback for: {messages[-1].content[:60]}...)"

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        # Non-streaming fallback for simple responses
        full = await self.complete(messages, system_prompt, temperature, max_tokens, task)
        for word in full.split():
            yield word + " "


# ------------------------------------------------------------------ #
#  Mock Provider (Fallback)
# ------------------------------------------------------------------ #

class MockProvider(BaseLLMProvider):
    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        last = messages[-1].content if messages else ""
        return (
            f"**DataWise AI** (Autonomous Data Scientist — Demo Mode)\n\n"
            f"Analysis of query: _{last[:160]}..._\n\n"
            f"To enable real LLM completions, configure `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` in your `.env`."
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        text = await self.complete(messages, system_prompt, temperature, max_tokens, task)
        for word in text.split():
            yield word + " "


# ------------------------------------------------------------------ #
#  Facade Dispatcher & Model Router
# ------------------------------------------------------------------ #

class LLMProvider:
    """
    Unified LLM router managing Gemini, OpenAI, Anthropic, and Mock providers.
    Routes queries to fast or capable models based on task complexity.
    """

    def __init__(self) -> None:
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

        self._active_provider = self._select_provider()
        logger.info(f"LLMProvider initialized with active backend: {self._active_provider.__class__.__name__}")

    def _select_provider(self) -> BaseLLMProvider:
        if self.gemini_key:
            return GeminiProvider(self.gemini_key)
        if self.openai_key:
            return OpenAIProvider(self.openai_key)
        if self.anthropic_key:
            return AnthropicProvider(self.anthropic_key)
        return MockProvider()

    async def complete(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> str:
        return await self._active_provider.complete(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            task=task,
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        task: Literal["fast", "capable"] = "fast",
    ) -> AsyncIterator[str]:
        async for chunk in self._active_provider.stream(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            task=task,
        ):
            yield chunk


# Singleton
llm_provider = LLMProvider()
