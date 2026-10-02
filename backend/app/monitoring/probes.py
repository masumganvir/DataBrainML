"""DataWise AI — Health & Readiness Probes

Provides deep dependencies verification without leaking secrets or credentials:
  - PostgreSQL connectivity (SELECT 1)
  - Redis connectivity (PING)
  - Object Storage bucket accessibility (S3/MinIO/Local)
"""

from __future__ import annotations

import time
from typing import Dict, Tuple
from sqlalchemy import text
from loguru import logger

from app.cache.redis_client import get_redis_manager
from app.db.session import engine
from app.storage.service import get_storage_service


async def check_database_health() -> Tuple[bool, dict]:
    """Verify PostgreSQL connectivity and query response time."""
    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return True, {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, {"status": "error", "error": "Database connection refused"}


async def check_redis_health() -> Tuple[bool, dict]:
    """Verify Redis cluster connectivity."""
    start = time.perf_counter()
    try:
        redis_mgr = get_redis_manager()
        info = await redis_mgr.check_health()
        latency_ms = (time.perf_counter() - start) * 1000
        info["latency_ms"] = round(latency_ms, 2)
        return info.get("status") in ("ok", "degraded"), info
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False, {"status": "error", "error": "Redis connection refused"}


def check_storage_health() -> Tuple[bool, dict]:
    """Verify Object Storage bucket access."""
    try:
        storage_svc = get_storage_service()
        info = storage_svc.check_health()
        return True, info
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return False, {"status": "error", "error": "Object storage unreachable"}
