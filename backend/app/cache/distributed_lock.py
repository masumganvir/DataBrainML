"""DataWise AI — Distributed Lock Concurrency Control

Prevents duplicate execution of expensive ML operations across multiple server instances:
  - dataset:{id}:processing
  - experiment:{id}:training
  - model:{id}:deployment
  - retraining:{model_id}
"""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from loguru import logger

from app.cache.redis_client import get_redis_manager


class LockAcquisitionError(Exception):
    """Raised when distributed lock cannot be acquired within the timeout."""
    pass


class DistributedLock:
    """Redis-backed distributed lock with safe token release."""

    def __init__(self, key: str, ttl_seconds: int = 120, timeout_seconds: float = 5.0):
        self.key = f"lock:{key}"
        self.ttl = ttl_seconds
        self.timeout = timeout_seconds
        self.token = str(uuid.uuid4())
        self._acquired = False
        self._redis_mgr = get_redis_manager()

    async def acquire(self) -> bool:
        client = await self._redis_mgr.get_client()
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            # Atomic set with NX and PX/EX
            if hasattr(client, "set"):
                # Check if it supports redis async client options
                try:
                    res = await client.set(self.key, self.token, ex=self.ttl, nx=True)
                    if res:
                        self._acquired = True
                        return True
                except TypeError:
                    # Fallback cache
                    existing = await client.get(self.key)
                    if not existing:
                        await client.set(self.key, self.token, ex=self.ttl)
                        self._acquired = True
                        return True

            await asyncio.sleep(0.1)

        raise LockAcquisitionError(f"Could not acquire distributed lock for resource: {self.key}")

    async def release(self) -> bool:
        if not self._acquired:
            return False

        client = await self._redis_mgr.get_client()
        try:
            # Safe token-based release via Lua script if Redis, or direct check
            lua_release = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            if hasattr(client, "eval"):
                await client.eval(lua_release, 1, self.key, self.token)
            else:
                curr = await client.get(self.key)
                if curr == self.token:
                    await client.delete(self.key)
            self._acquired = False
            return True
        except Exception as e:
            logger.warning(f"Error releasing distributed lock {self.key}: {e}")
            return False


@asynccontextmanager
async def distributed_lock(
    resource_key: str,
    ttl_seconds: int = 120,
    timeout_seconds: float = 5.0,
) -> AsyncGenerator[DistributedLock, None]:
    """Async context manager for acquiring and safely releasing distributed locks."""
    lock = DistributedLock(resource_key, ttl_seconds, timeout_seconds)
    await lock.acquire()
    try:
        yield lock
    finally:
        await lock.release()
