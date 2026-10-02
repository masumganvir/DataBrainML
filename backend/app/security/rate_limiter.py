"""
DataWise AI — API Rate Limiting Middleware

Sliding window rate limiter to protect expensive analytical and LLM routes
from denial-of-service and runaway client loops.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class SlidingWindowRateLimiter:
    """Sliding-window counter for rate limiting per client IP."""

    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds

        # Evict timestamps older than the window
        timestamps = [ts for ts in self._requests[client_ip] if ts > window_start]
        self._requests[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            retry_after = int(timestamps[0] + self.window_seconds - now) + 1
            return False, max(1, retry_after)

        self._requests[client_ip].append(now)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware enforcing rate limits on API requests."""

    def __init__(self, app, max_requests: int = 240, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exempt health check and static endpoints
        path = request.url.path
        if path.startswith("/api/v1/health") or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        allowed, retry_after = self.limiter.is_allowed(client_ip)

        if not allowed:
            return Response(
                content=f'{{"detail": "Rate limit exceeded. Try again in {retry_after} seconds."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
