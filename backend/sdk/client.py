"""
Agentic AutoML Intelligence Platform — Python SDK Client
Client library for integrating Agentic AutoML predictions and features into external software.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx


class AgenticAutoMLClient:
    """Official Python Client for Agentic AutoML Intelligence Platform."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers, timeout=timeout)

    def predict(
        self,
        features: Dict[str, Any],
        entity_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform real-time model inference with optional feature store enrichment."""
        payload = {"features": features}
        if entity_id:
            payload["entity_id"] = entity_id
        if request_id:
            payload["request_id"] = request_id

        res = self.client.post("/api/v1/predict", json=payload)
        res.raise_for_status()
        return res.json()

    def batch_predict(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch prediction."""
        res = self.client.post("/api/v1/batch-predict", json={"records": records})
        res.raise_for_status()
        return res.json()

    def get_online_features(self, entity_id: str) -> Dict[str, Any]:
        """Query real-time feature store vector for an entity."""
        res = self.client.get(f"/api/v1/features/{entity_id}")
        res.raise_for_status()
        return res.json()

    def ingest_cdc_event(
        self,
        source: str,
        entity_id: str,
        payload: Dict[str, Any],
        operation: str = "INSERT",
    ) -> Dict[str, Any]:
        """Stream a Change Data Capture event into the platform."""
        body = {
            "source": source,
            "entity_id": entity_id,
            "operation": operation,
            "payload": payload,
        }
        res = self.client.post("/api/v1/cdc/events", json=body)
        res.raise_for_status()
        return res.json()

    def get_model_health(self, model_id: str = "primary") -> Dict[str, Any]:
        """Retrieve real-time telemetry, drift status, and SLA health report."""
        res = self.client.get(f"/api/v1/models/{model_id}/health")
        res.raise_for_status()
        return res.json()

    def rollback_model(self, model_id: str = "primary", target_version: Optional[str] = None, reason: str = "") -> Dict[str, Any]:
        """Execute instant rollback to previous stable model version."""
        res = self.client.post(
            f"/api/v1/models/{model_id}/rollback",
            json={"target_version": target_version, "reason": reason},
        )
        res.raise_for_status()
        return res.json()

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
