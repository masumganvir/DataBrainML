# Distributed Rate Limiting & Compute Protection

## 1. Purpose
Protects the platform from abusive traffic, runaway client loops, and compute starvation on expensive ML operations (Optuna hyperparameter tuning, model training, and dataset profiling).

## 2. Multi-Tiered Rate Limiting Architecture
- **Tier 1 (Global IP)**: 120 requests / min / IP.
- **Tier 2 (Authentication Routes)**: 10 requests / min / IP to prevent brute-force credential stuffing.
- **Tier 3 (Upload Routes)**: 20 uploads / hour / user.
- **Tier 4 (ML Training Routes)**: 10 training runs / hour / user.
- **Tier 5 (Inference Endpoints)**: 300 requests / min.

## 3. Atomic Sliding Window Algorithm
Implemented via Redis sorted sets (ZSET) and a Lua script (`SLIDING_WINDOW_LUA`):
1. `ZREMRANGEBYSCORE key 0 (now - window)`
2. `count = ZCARD key`
3. If `count < max_requests`: records request (`ZADD`), resets `EXPIRE`, allows request.
4. If exceeded: finds timestamp of oldest hit, calculates precise `Retry-After`, and returns HTTP 429.

## 4. HTTP 429 Response Format
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please slow down.",
  "retry_after": 30,
  "request_id": "c1f7b028-1111-4f40-8b1a-b6058495df22"
}
```
Headers emitted:
- `Retry-After`: 30
- `X-RateLimit-Limit`: 120
- `X-RateLimit-Remaining`: 0
- `X-RateLimit-Reset`: 1759100000
- `X-Request-ID`: UUID

## 5. Idempotency Keys
Expensive endpoints support `Idempotency-Key` header. Requests with duplicate keys within 1 hour return cached responses without re-executing background compute.
