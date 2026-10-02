"""
Agentic AutoML Intelligence Platform — Model Health Dashboard
Aggregates production runtime telemetry, drift status, SLA, and model lifecycle metrics.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelHealthReport(BaseModel):
    model_id: str
    active_version: str
    status: str                                  # healthy | degraded | critical
    uptime_seconds: float
    total_predictions: int = 0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    drift_status: str = "stable"                 # stable | warning | critical
    drift_score: float = 0.0
    latest_feature_drift: Dict[str, Any] = Field(default_factory=dict)
    concept_drift_status: str = "stable"
    prediction_distribution: Dict[str, float] = Field(default_factory=dict)
    feature_freshness_sla_met: bool = True
    online_learning_enabled: bool = False
    last_incremental_update: Optional[datetime] = None
    last_retraining_timestamp: Optional[datetime] = None
    shadow_model_active: bool = False
    shadow_version: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelHealthMonitor:
    """Collects and aggregates model health statistics."""

    def __init__(self, model_id: str = "default_model", active_version: str = "v1.0.0"):
        self.model_id = model_id
        self.active_version = active_version
        self.start_time = time.time()
        self._latencies: List[float] = []
        self._prediction_counts: Dict[str, int] = {}
        self._total_requests: int = 0
        self._errors: int = 0

    def record_prediction(self, prediction_label: str, latency_ms: float, is_error: bool = False):
        self._total_requests += 1
        if is_error:
            self._errors += 1
        else:
            self._latencies.append(latency_ms)
            if len(self._latencies) > 5000:
                self._latencies = self._latencies[-2500:]

            key = str(prediction_label)
            self._prediction_counts[key] = self._prediction_counts.get(key, 0) + 1

    def get_health_report(
        self,
        drift_report: Optional[Dict[str, Any]] = None,
        concept_drift_report: Optional[Dict[str, Any]] = None,
        online_learning_active: bool = False,
        shadow_version: Optional[str] = None,
    ) -> ModelHealthReport:
        uptime = time.time() - self.start_time
        err_rate = (self._errors / self._total_requests) if self._total_requests > 0 else 0.0

        avg_lat = float(sum(self._latencies) / len(self._latencies)) if self._latencies else 0.0
        sorted_lat = sorted(self._latencies) if self._latencies else [0.0]
        p95 = float(sorted_lat[int(len(sorted_lat) * 0.95)]) if sorted_lat else 0.0
        p99 = float(sorted_lat[int(len(sorted_lat) * 0.99)]) if sorted_lat else 0.0

        # Prediction distribution percentage
        pred_dist = {}
        valid_preds = sum(self._prediction_counts.values())
        if valid_preds > 0:
            pred_dist = {k: round(v / valid_preds, 4) for k, v in self._prediction_counts.items()}

        drift_score = 0.0
        drift_status = "stable"
        if drift_report:
            drift_score = drift_report.get("drift_ratio", 0.0)
            if drift_report.get("overall_severity") == "high":
                drift_status = "critical"
            elif drift_report.get("overall_severity") == "medium":
                drift_status = "warning"

        concept_status = "stable"
        if concept_drift_report and concept_drift_report.get("concept_drift_detected"):
            concept_status = "critical" if concept_drift_report.get("severity") == "high" else "warning"

        overall_status = "healthy"
        if err_rate > 0.05 or drift_status == "critical" or concept_status == "critical":
            overall_status = "critical"
        elif err_rate > 0.01 or drift_status == "warning" or concept_status == "warning":
            overall_status = "degraded"

        return ModelHealthReport(
            model_id=self.model_id,
            active_version=self.active_version,
            status=overall_status,
            uptime_seconds=round(uptime, 1),
            total_predictions=self._total_requests,
            average_latency_ms=round(avg_lat, 2),
            p95_latency_ms=round(p95, 2),
            p99_latency_ms=round(p99, 2),
            error_rate=round(err_rate, 4),
            drift_status=drift_status,
            drift_score=drift_score,
            latest_feature_drift=drift_report or {},
            concept_drift_status=concept_status,
            prediction_distribution=pred_dist,
            feature_freshness_sla_met=True,
            online_learning_enabled=online_learning_active,
            shadow_model_active=bool(shadow_version),
            shadow_version=shadow_version,
        )


model_health_monitor = ModelHealthMonitor()
