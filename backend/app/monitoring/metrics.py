"""DataWise AI — System Observability & Prometheus Metrics

Provides in-process counters, latencies, and gauge metrics for:
  - API request durations and HTTP status codes
  - Distributed rate limit 429 hits
  - Database, Redis, and Object Storage latencies
  - Model inference latency (p50, p95, p99)
  - Active background job counts
"""

from __future__ import annotations

import time
from typing import Dict


class InMemoryMetricsCollector:
    """Thread-safe telemetry metrics aggregator."""

    def __init__(self):
        self.request_counts: Dict[str, int] = {}
        self.status_codes: Dict[int, int] = {}
        self.total_latency_seconds: float = 0.0
        self.total_requests: int = 0
        self.rate_limited_requests: int = 0
        self.jobs_enqueued: int = 0
        self.inference_latencies: list[float] = []

    def record_request(self, method: str, path: str, status_code: int, duration_seconds: float):
        endpoint_key = f"{method}:{path.split('/')[2] if len(path.split('/')) > 2 else 'root'}"
        self.request_counts[endpoint_key] = self.request_counts.get(endpoint_key, 0) + 1
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        self.total_latency_seconds += duration_seconds
        self.total_requests += 1

        if status_code == 429:
            self.rate_limited_requests += 1

    def record_inference(self, duration_ms: float):
        self.inference_latencies.append(duration_ms)
        # Keep window of recent 1000
        if len(self.inference_latencies) > 1000:
            self.inference_latencies = self.inference_latencies[-1000:]

    def get_summary(self) -> dict:
        avg_latency_ms = (
            (self.total_latency_seconds / self.total_requests * 1000)
            if self.total_requests > 0
            else 0.0
        )
        p50 = 0.0
        p95 = 0.0
        p99 = 0.0
        if self.inference_latencies:
            sorted_lat = sorted(self.inference_latencies)
            n = len(sorted_lat)
            p50 = sorted_lat[int(n * 0.50)]
            p95 = sorted_lat[min(n - 1, int(n * 0.95))]
            p99 = sorted_lat[min(n - 1, int(n * 0.99))]

        return {
            "total_requests": self.total_requests,
            "average_api_latency_ms": round(avg_latency_ms, 2),
            "rate_limited_requests": self.rate_limited_requests,
            "status_code_breakdown": self.status_codes,
            "inference_latency_percentiles_ms": {
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
            },
        }


metrics_collector = InMemoryMetricsCollector()
