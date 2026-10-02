"""DataWise AI — Distributed Rate Limiting Middleware

Enforces tiered rate limits using the Redis-backed distributed rate limiter:
  - Auth routes: 10 requests / min / IP
  - Prediction routes: 300 requests / min
  - General API: 120 requests / min

Returns HTTP 429 with standard headers and JSON payload when limit is exceeded.
"""

from __future__ import annotations

import json
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import get_settings
from app.rate_limit.limiter import get_rate_limiter


class DistributedRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed Redis-backed rate limiting middleware for FastAPI."""

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.limiter = get_rate_limiter()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exempt health probes, documentation, and CORS preflights
        path = request.url.path
        if (
            path.startswith("/health")
            or path.startswith("/api/docs")
            or path.startswith("/api/redoc")
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        # Determine identifier: Authenticated user / API key or IP
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get("X-API-Key", "")
        client_ip = request.client.host if request.client else "127.0.0.1"

        if api_key_header:
            identifier = f"key:{api_key_header[:8]}"
        elif auth_header.startswith("Bearer "):
            # Token prefix as transient identifier
            identifier = f"token:{auth_header[7:20]}"
        else:
            identifier = f"ip:{client_ip}"

        # Determine rate limit based on endpoint path
        if "auth" in path or "login" in path:
            limit = self.settings.rate_limit_auth
            window = 60
        elif "predict" in path or "inference" in path:
            limit = self.settings.rate_limit_prediction
            window = 60
        elif "upload" in path:
            limit = self.settings.rate_limit_upload
            window = 3600
        elif "train" in path:
            limit = self.settings.rate_limit_training
            window = 3600
        else:
            limit = self.settings.rate_limit_default
            window = 60

        endpoint_tag = path.split("/")[2] if len(path.split("/")) > 2 else "root"
        allowed, remaining, retry_after = await self.limiter.is_allowed(
            identifier=identifier,
            endpoint=endpoint_tag,
            max_requests=limit,
            window_seconds=window,
        )

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        if not allowed:
            payload = {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down.",
                "retry_after": retry_after,
                "request_id": request_id,
            }
            return Response(
                content=json.dumps(payload),
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    "X-Request-ID": request_id,
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-Request-ID"] = request_id
        return response
