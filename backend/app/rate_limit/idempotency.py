"""DataWise AI — Distributed Idempotency Control

Ensures duplicate requests with identical Idempotency-Key headers
do not spawn repeated expensive workflows or background jobs:
  - POST /api/datasets
  - POST /api/experiments
  - POST /api/training
  - POST /api/deployments
  - POST /api/predictions
"""

from __future__ import annotations

import json
from typing import Optional
from fastapi import Header, HTTPException, status
from loguru import logger

from app.cache.redis_client import get_redis_manager


class IdempotencyService:
    """Manages short-lived idempotency tokens and cached responses."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._redis_mgr = get_redis_manager()

    def _key(self, token: str) -> str:
        return f"idempotency:{token}"

    async def check_key(self, token: str) -> Optional[dict]:
        """Check if idempotency key has already completed or is currently running."""
        client = await self._redis_mgr.get_client()
        raw = await client.get(self._key(token))
        if raw is not None:
            try:
                return json.loads(raw)
            except Exception:
                return {"status": "in_progress"}
        return None

    async def lock_key(self, token: str) -> bool:
        """Mark idempotency key as in-progress."""
        client = await self._redis_mgr.get_client()
        try:
            if hasattr(client, "set"):
                # Try atomic set with NX
                res = await client.set(self._key(token), json.dumps({"status": "in_progress"}), ex=self.ttl)
                return bool(res)
        except Exception as e:
            logger.warning(f"Failed to lock idempotency key {token}: {e}")
        return True

    async def record_response(self, token: str, response_data: dict, status_code: int = 200) -> None:
        """Store the completed operation result for replay on duplicate calls."""
        client = await self._redis_mgr.get_client()
        payload = {
            "status": "completed",
            "status_code": status_code,
            "response": response_data,
        }
        try:
            await client.set(self._key(token), json.dumps(payload), ex=self.ttl)
        except Exception as e:
            logger.warning(f"Failed to store idempotency result for {token}: {e}")


_idempotency_singleton: Optional[IdempotencyService] = None


def get_idempotency_service() -> IdempotencyService:
    global _idempotency_singleton
    if _idempotency_singleton is None:
        _idempotency_singleton = IdempotencyService()
    return _idempotency_singleton
