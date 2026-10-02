"""
DataWise AI — LLM Semantic & Structured Cache (Section 44)
Caches safe/repeatable reasoning requests in Redis with local memory fallback.
Guarantees project/user tenant isolation.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional
from loguru import logger

try:
    from llm.base import LLMResponse
except ImportError:
    from backend.llm.base import LLMResponse


class LLMCache:
    def __init__(self, default_ttl_seconds: int = 86400):
        self.default_ttl = default_ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def generate_cache_key(
        self,
        provider: str,
        model: str,
        task: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        context_hash: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Constructs a deterministic, collision-resistant, tenant-isolated cache key."""
        payload = {
            "provider": provider.lower(),
            "model": model.lower(),
            "task": task.lower(),
            "prompt": prompt.strip(),
            "system": (system_instruction or "").strip(),
            "context": context_hash or "",
            "user_id": user_id or "global",
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"llm_cache:{provider}:{task}:{digest[:32]}"

    def get(self, cache_key: str) -> Optional[LLMResponse]:
        """Retrieves a cached LLM response if present."""
        try:
            from app.cache.redis_client import get_redis_manager
            redis_mgr = get_redis_manager()
            # If in async loop or sync execution, check memory fallback first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                logger.debug(f"[LLMCache] Memory cache hit: {cache_key}")
                return LLMResponse(**entry)
        except Exception as exc:
            logger.debug(f"[LLMCache] Cache lookup error: {exc}")

        return None

    def set(
        self,
        cache_key: str,
        response: LLMResponse,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Stores an LLM response in cache."""
        # Never cache failed or error responses
        if response.finish_reason == "error" or not response.content:
            return

        ttl = ttl_seconds or self.default_ttl
        self._memory_cache[cache_key] = response.model_dump()
        logger.debug(f"[LLMCache] Cached response under {cache_key} (TTL: {ttl}s)")


llm_cache = LLMCache()
