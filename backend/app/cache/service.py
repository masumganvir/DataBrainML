"""DataWise AI — Result Caching Service

Caches safe deterministic ML outputs:
  - Dataset schema & summary profiles
  - Visualization metadata
  - Model metadata
  - Reports
  
Invalidates on model promotions, version changes, and dataset updates.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from loguru import logger

from app.cache.redis_client import get_redis_manager


class CacheService:
    """High-performance Redis-backed caching service with TTL and key-prefix invalidation."""

    def __init__(self, prefix: str = "cache:"):
        self.prefix = prefix
        self._redis_mgr = get_redis_manager()

    def _format_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Fetch and deserialize JSON cached value."""
        client = await self._redis_mgr.get_client()
        raw = await client.get(self._format_key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Serialize and store value in cache with TTL."""
        client = await self._redis_mgr.get_client()
        try:
            payload = json.dumps(value)
            await client.set(self._format_key(key), payload, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Failed to cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove single key from cache."""
        client = await self._redis_mgr.get_client()
        res = await client.delete(self._format_key(key))
        return bool(res)

    async def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys matching prefix."""
        client = await self._redis_mgr.get_client()
        pattern = f"{self.prefix}{prefix}*"
        count = 0
        if hasattr(client, "keys"):
            keys = await client.keys(pattern)
            if keys:
                count = await client.delete(*keys)
        return count


_cache_singleton: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Singleton getter for CacheService."""
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = CacheService()
    return _cache_singleton
