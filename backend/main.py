"""
DataWise AI — FastAPI Enterprise Application Entry Point

Startup sequence:
  1. Load validated settings
  2. Initialize database metadata / migrations
  3. Mount CORS middleware with strict origin validation
  4. Mount Distributed Rate Limiting (Redis-backed atomic sliding window)
  5. Mount Structured Telemetry, Metrics & Request-ID Middleware
  6. Register Enterprise API routers
  7. Expose Container Health, Liveness, and Deep Readiness Probes
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure both backend and workspace root are in sys.path
_backend_dir = Path(__file__).resolve().parent
_root_dir = _backend_dir.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.cache.redis_client import get_redis_manager
from app.config.settings import get_settings
from app.db.session import init_db
from app.monitoring.metrics import metrics_collector
from app.monitoring.probes import (
    check_database_health,
    check_redis_health,
    check_storage_health,
)
from app.rate_limit.middleware import DistributedRateLimitMiddleware

settings = get_settings()


# ------------------------------------------------------------------ #
#  Lifespan (startup / shutdown)
# ------------------------------------------------------------------ #

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup; cleanly dispose on shutdown."""
    logger.info(f"Starting DataWise AI Enterprise Platform [{settings.app_env}]")
    await init_db()
    logger.info("Database initialized successfully.")
    
    redis_mgr = get_redis_manager()
    await redis_mgr.get_client()
    
    yield

    logger.info("DataWise AI platform shutting down. Disposing connection pools...")
    await redis_mgr.close()
    logger.info("Shutdown complete.")


# ------------------------------------------------------------------ #
#  App Factory
# ------------------------------------------------------------------ #

def create_app() -> FastAPI:
    app = FastAPI(
        title="DataWise AI Enterprise Platform",
        description="Production Database, Redis, Object Storage, and Agentic AI AutoML Engine",
        version="1.0.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── Middleware Order Note ──────────────────────────────────────────────
    # Starlette runs middlewares in LIFO (last added = first executed) order.
    # CORS must execute FIRST so OPTIONS preflights are answered immediately.
    # Therefore CORS is added LAST (runs first in LIFO execution order).
    # ──────────────────────────────────────────────────────────────────────

    # 1. Rate Limiting  (added first → runs second in LIFO)
    app.add_middleware(DistributedRateLimitMiddleware)

    # 2. CORS  (added last → runs FIRST in LIFO)
    # In development we allow all origins to avoid localhost vs 127.0.0.1 mismatches.
    # In production this is replaced by the strict CORS_ORIGINS env var list.
    _cors_origins = ["*"] if settings.is_development else settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False if "*" in _cors_origins else True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-Remaining"],
    )


    # 3. Telemetry, Request ID & Latency Middleware
    @app.middleware("http")
    async def telemetry_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = f"{elapsed:.4f}s"

        # Record metrics
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=elapsed,
        )
        return response

    # ------------------------------------------------------------------ #
    #  Routers
    # ------------------------------------------------------------------ #
    from app.api.router import api_router
    app.include_router(api_router, prefix="/api")
    app.include_router(api_router, prefix="/api/v1")

    # ------------------------------------------------------------------ #
    #  Global Exception Handler & Confidentiality Gate
    # ------------------------------------------------------------------ #
    from recovery.error_detector import ErrorDetector
    from recovery.error_classifier import ErrorClassifier
    from recovery.safe_error_formatter import SafeErrorFormatter
    from recovery.context_sanitizer import OutputSecurityGate

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Detect and normalize without leaking secrets into logs or objects
        err_obj = ErrorDetector.detect_and_normalize(
            exception=exc,
            stage=request.url.path,
            agent_id="api_gateway",
            workflow_id=req_id,
        )
        classified = ErrorClassifier.classify(err_obj)
        logger.error(
            f"Handled exception on {request.url.path} [ErrorID={classified.error_id} Code={classified.error_code.value}]"
        )
        safe_response = SafeErrorFormatter.format_api_response(
            error_id=classified.error_id,
            error_code=classified.error_code,
            message=classified.safe_message or "An unexpected system error occurred.",
            hint=classified.recommended_action or "Please verify request parameters.",
            retryable=classified.retryable,
            reference_id=req_id,
        )
        # Ensure additional top-level request_id field for backward compatibility
        safe_response["request_id"] = req_id
        resp = JSONResponse(
            status_code=500,
            content=OutputSecurityGate.sanitize(safe_response),
        )
        origin = request.headers.get("origin")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "*"
        else:
            resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["X-Request-ID"] = req_id
        return resp

    return app


app = create_app()


# ------------------------------------------------------------------ #
#  Container & Orchestration Health Probes
# ------------------------------------------------------------------ #

@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe for container orchestration."""
    return {
        "status": "ok",
        "service": "DataWise AI",
        "version": "1.0.0",
        "environment": settings.app_env,
    }



@app.get("/health/live", tags=["System"])
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["System"])
async def readiness_probe(response: Response):
    """Deep readiness probe verifying PostgreSQL, Redis, and Object Storage."""
    db_ok, db_info = await check_database_health()
    redis_ok, redis_info = await check_redis_health()
    storage_ok, storage_info = check_storage_health()

    all_ready = db_ok and redis_ok and storage_ok
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ready else "unhealthy",
        "components": {
            "database": db_info,
            "redis": redis_info,
            "storage": storage_info,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.app_log_level.lower(),
    )
