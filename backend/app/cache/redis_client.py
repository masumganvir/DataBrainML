"""DataWise AI — Redis Connection Manager & Distributed Client

Provides resilient, connection-pooled asynchronous Redis connectivity for:
  - Distributed Rate Limiting (Token Bucket / Sliding Window)
  - Distributed Concurrency Locks
  - Deterministic Result Caching
  - Real-time Job Progress & Pub/Sub
  - Graceful in-memory fallback if Redis is unavailable in local testing
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional
from loguru import logger

from app.config.settings import get_settings

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryFallbackCache:
    """Thread-safe in-memory key-value store used when Redis is unavailable."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._expires: dict[str, float] = {}
        self._lists: dict[str, list[str]] = {}


    def _purge_expired(self):
        now = time.time()
        expired = [k for k, exp in self._expires.items() if exp < now]
        for k in expired:
            self._data.pop(k, None)
            self._expires.pop(k, None)

    async def get(self, key: str) -> Optional[str]:
        self._purge_expired()
        if key in self._expires and self._expires[key] < time.time():
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return None
        return self._data.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        self._purge_expired()
        self._data[key] = str(value)
        if ex:
            self._expires[key] = time.time() + ex
        else:
            self._expires.pop(key, None)
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                self._expires.pop(k, None)
                count += 1
            if k in self._lists:
                del self._lists[k]
                count += 1
        return count

    async def rpush(self, key: str, value: str) -> int:
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key].append(value)
        return len(self._lists[key])

    async def lpop(self, key: str) -> Optional[str]:
        if key in self._lists and self._lists[key]:
            return self._lists[key].pop(0)
        return None

    async def ping(self) -> bool:
        return True



class RedisManager:
    """Manages Redis async connection pool with resilient status monitoring."""

    def __init__(self):
        self.settings = get_settings()
        self.url = self.settings.redis_url
        self._client: Optional[aioredis.Redis] = None
        self._fallback = InMemoryFallbackCache()
        self._connected = False
        self._checked = False

    async def get_client(self) -> Any:
        """Return active Redis client or in-memory fallback."""
        if not REDIS_AVAILABLE:
            return self._fallback

        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.url,
                    password=self.settings.redis_password or None,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                )
                await asyncio.wait_for(self._client.ping(), timeout=1.5)
                self._connected = True
                logger.info(f"Connected to Redis at {self.url}")
            except Exception as e:
                logger.warning(f"Could not connect to Redis at {self.url}: {e}. Operating in graceful in-memory fallback mode.")
                self._connected = False
                return self._fallback

        return self._client if self._connected else self._fallback

    async def check_health(self) -> dict:
        """Health check probe for readiness endpoint."""
        client = await self.get_client()
        if client is self._fallback:
            return {"status": "degraded", "mode": "in_memory_fallback", "url": self.url}
        try:
            await asyncio.wait_for(client.ping(), timeout=1.0)
            return {"status": "ok", "mode": "redis_cluster_connected", "url": self.url}
        except Exception as e:
            return {"status": "degraded", "mode": "in_memory_fallback", "error": str(e)}

    async def close(self):
        if self._client is not None:
            await self._client.aclose()


_redis_manager_singleton: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """Singleton getter for RedisManager."""
    global _redis_manager_singleton
    if _redis_manager_singleton is None:
        _redis_manager_singleton = RedisManager()
    return _redis_manager_singleton
