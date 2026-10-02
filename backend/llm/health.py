"""
DataWise AI — LLM Health & Observability Service
Provides deep health inspection across all AI providers (Gemini, Groq, Cloudflare, Ollama).
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict
from pydantic import BaseModel

try:
    from llm.circuit_breaker import circuit_registry, CircuitState
    from llm.quota_manager import quota_manager
except ImportError:
    from backend.llm.circuit_breaker import circuit_registry, CircuitState
    from backend.llm.quota_manager import quota_manager


class ProviderHealthStatus(BaseModel):
    provider: str
    status: str  # healthy, degraded, open_circuit, unconfigured, offline
    configured: bool
    circuit_state: str
    failure_count: int
    average_latency: float
    total_requests: int
    rate_limit_429s: int
    last_error: str = ""


class AIInfrastructureHealth(BaseModel):
    overall_status: str  # healthy, degraded, critical
    primary_provider: str
    providers: Dict[str, ProviderHealthStatus]
    timestamp: float


def check_provider_health(provider_name: str) -> ProviderHealthStatus:
    name = provider_name.lower()
    breaker = circuit_registry.get_breaker(name)
    metrics = quota_manager.get_metrics(name)

    # Check configuration
    is_configured = False
    if name == "gemini":
        is_configured = bool(os.getenv("GEMINI_API_KEY"))
    elif name == "groq":
        is_configured = bool(os.getenv("GROQ_API_KEY"))
    elif name == "cloudflare":
        token = os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CLAUDEFLARE_AI_WORKER_API_KEY")
        is_configured = bool(token)
    elif name == "ollama":
        is_configured = True

    # Determine status
    if not is_configured:
        status = "unconfigured"
    elif breaker.state == CircuitState.OPEN:
        status = "open_circuit"
    elif breaker.state == CircuitState.HALF_OPEN or metrics.rate_limit_429_count > 0:
        status = "degraded"
    else:
        status = "healthy"

    return ProviderHealthStatus(
        provider=name,
        status=status,
        configured=is_configured,
        circuit_state=breaker.state.value,
        failure_count=breaker.failure_count,
        average_latency=metrics.average_latency_seconds,
        total_requests=metrics.total_requests,
        rate_limit_429s=metrics.rate_limit_429_count,
        last_error=metrics.last_error_message or "",
    )


def get_ai_health_report() -> AIInfrastructureHealth:
    providers = ["gemini", "groq", "cloudflare", "ollama"]
    statuses = {p: check_provider_health(p) for p in providers}

    # If primary (gemini) is healthy, overall is healthy; if both gemini & groq open, critical
    if statuses["gemini"].status == "healthy":
        overall = "healthy"
    elif statuses["groq"].status == "healthy" or statuses["cloudflare"].status == "healthy":
        overall = "degraded"
    else:
        overall = "critical"

    return AIInfrastructureHealth(
        overall_status=overall,
        primary_provider=os.getenv("LLM_PROVIDER", "gemini"),
        providers=statuses,
        timestamp=time.time(),
    )
