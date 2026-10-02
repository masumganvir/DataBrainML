"""DataWise AI — Distributed Rate Limiting & Idempotency Tests."""

import pytest
from app.rate_limit.limiter import get_rate_limiter
from app.rate_limit.idempotency import get_idempotency_service


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter_permits():
    limiter = get_rate_limiter()
    # Test allowed request
    allowed, remaining, retry_after = await limiter.is_allowed(
        identifier="test_user_1",
        endpoint="datasets",
        max_requests=5,
        window_seconds=10,
    )
    assert allowed is True
    assert retry_after == 0


@pytest.mark.asyncio
async def test_idempotency_workflow():
    service = get_idempotency_service()
    key = "idem-test-token-12345"

    # Initially not present
    existing = await service.check_key(key)
    assert existing is None

    # Lock key
    locked = await service.lock_key(key)
    assert locked is True

    # Record response
    await service.record_response(key, {"dataset_id": "ds-999", "status": "uploaded"}, 201)

    # Subsequent check should return cached result
    cached = await service.check_key(key)
    assert cached is not None
    assert cached["status"] == "completed"
    assert cached["response"]["dataset_id"] == "ds-999"
