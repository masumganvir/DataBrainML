"""
DataWise AI — LLM Quota & Usage Manager
Tracks request volumes, token usage, latency, 429 rate-limiting events,
and cooldown periods across all integrated providers.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProviderUsageMetrics(BaseModel):
    provider_name: str
    total_requests: int = 0
    total_tokens: int = 0
    total_errors: int = 0
    rate_limit_429_count: int = 0
    last_request_time: float = 0.0
    last_success_time: float = 0.0
    last_error_time: float = 0.0
    last_error_message: Optional[str] = None
    remaining_quota: Optional[int] = None
    average_latency_seconds: float = 0.0
    latency_history: list[float] = Field(default_factory=list, exclude=True)


class QuotaManager:
    def __init__(self):
        self._metrics: Dict[str, ProviderUsageMetrics] = {}

    def get_metrics(self, provider_name: str) -> ProviderUsageMetrics:
        name = provider_name.lower()
        if name not in self._metrics:
            self._metrics[name] = ProviderUsageMetrics(provider_name=name)
        return self._metrics[name]

    def record_call(
        self,
        provider_name: str,
        duration_seconds: float,
        tokens_used: Optional[int] = None,
        is_error: bool = False,
        is_429: bool = False,
        error_message: Optional[str] = None,
        remaining_quota: Optional[int] = None,
    ) -> None:
        m = self.get_metrics(provider_name)
        now = time.time()
        m.total_requests += 1
        m.last_request_time = now

        if tokens_used:
            m.total_tokens += tokens_used

        if is_error:
            m.total_errors += 1
            m.last_error_time = now
            m.last_error_message = error_message
            if is_429:
                m.rate_limit_429_count += 1
        else:
            m.last_success_time = now
            # Update moving average latency
            m.latency_history.append(duration_seconds)
            if len(m.latency_history) > 50:
                m.latency_history.pop(0)
            m.average_latency_seconds = round(sum(m.latency_history) / len(m.latency_history), 4)

        if remaining_quota is not None:
            m.remaining_quota = remaining_quota

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        return {name: m.model_dump() for name, m in self._metrics.items()}


quota_manager = QuotaManager()
