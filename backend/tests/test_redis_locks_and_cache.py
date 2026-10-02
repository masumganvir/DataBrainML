"""DataWise AI — Redis Distributed Locks & Cache Tests."""

import pytest
from app.cache.distributed_lock import distributed_lock
from app.cache.service import get_cache_service


@pytest.mark.asyncio
async def test_distributed_lock_acquire_and_release():
    resource = "experiment:123:training"
    async with distributed_lock(resource, ttl_seconds=10, timeout_seconds=1.0) as lock:
        assert lock.token is not None
        assert lock._acquired is True


@pytest.mark.asyncio
async def test_deterministic_cache_service():
    cache = get_cache_service()
    key = "model_schema:xgboost_v1"
    data = {"columns": ["age", "fare"], "types": ["float", "float"]}

    await cache.set(key, data, ttl_seconds=60)
    fetched = await cache.get(key)
    assert fetched == data

    await cache.delete(key)
    deleted = await cache.get(key)
    assert deleted is None
