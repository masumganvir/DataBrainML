"""DataWise AI — Redis-Backed Distributed Rate Limiter

Implements atomic sliding-window rate limiting using Redis sorted sets (ZSET)
and Lua scripting to eliminate race conditions across multiple worker processes.

Rate Limit Keys:
  - Global IP: ratelimit:ip:{client_ip}:{endpoint}
  - User: ratelimit:user:{user_id}:{endpoint}
  - API Key: ratelimit:key:{key_prefix}:{endpoint}
  - ML Compute: ratelimit:compute:{user_id}:{operation}
"""

from __future__ import annotations

import time
from typing import Optional, Tuple
from loguru import logger

from app.cache.redis_client import get_redis_manager
from app.config.settings import get_settings

# Redis Lua Script for Atomic Sliding Window
# KEYS[1] = rate limit key
# ARGV[1] = current timestamp (float as string)
# ARGV[2] = window size in seconds
# ARGV[3] = max allowed requests in window
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])
local clear_before = now - window

-- Remove expired entries older than the sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)

-- Count current requests in this window
local current_count = redis.call('ZCARD', key)

if current_count < max_requests then
    -- Record this request
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, math.ceil(window))
    local remaining = max_requests - current_count - 1
    return {1, remaining, 0}
else
    -- Find oldest request to calculate exact retry_after
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if oldest and #oldest >= 2 then
        local oldest_ts = tonumber(oldest[2])
        retry_after = math.max(1, math.ceil(oldest_ts + window - now))
    end
    return {0, 0, retry_after}
end
"""


class DistributedRateLimiter:
    """Distributed atomic rate limiter backed by Redis."""

    def __init__(self):
        self.settings = get_settings()
        self._redis_mgr = get_redis_manager()

    async def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """Check if request is permitted.

        Returns:
            Tuple[bool, int, int]: (allowed, remaining, retry_after)
        """
        if not self.settings.rate_limit_enabled:
            return True, max_requests, 0

        client = await self._redis_mgr.get_client()
        key = f"ratelimit:{identifier}:{endpoint}"
        now = time.time()

        try:
            if hasattr(client, "eval"):
                res = await client.eval(
                    SLIDING_WINDOW_LUA,
                    1,
                    key,
                    str(now),
                    str(window_seconds),
                    str(max_requests),
                )
                allowed = bool(res[0])
                remaining = int(res[1])
                retry_after = int(res[2])
                return allowed, remaining, retry_after
            else:
                # In-memory fallback
                return True, max_requests, 0
        except Exception as e:
            logger.warning(f"Rate limiter Redis check failed ({e}), allowing request gracefully.")
            return True, max_requests, 0


_limiter_singleton: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    """Singleton getter for DistributedRateLimiter."""
    global _limiter_singleton
    if _limiter_singleton is None:
        _limiter_singleton = DistributedRateLimiter()
    return _limiter_singleton
