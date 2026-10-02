"""
Agentic AutoML Intelligence Platform — API Integration Tests
Tests for real-time prediction, connectors, feature store, CDC, and shadow routes via FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from deployment.shadow_manager import deployment_manager
import numpy as np


class DummyAPIModel:
    def predict(self, X):
        return np.array([42.0] * len(X))


@pytest.fixture
def client():
    # Setup active model in deployment manager
    deployment_manager.register_version("v1.0.0", DummyAPIModel(), set_active=True)
    with TestClient(app) as c:
        yield c


def test_api_realtime_predict(client):
    res = client.post(
        "/api/v1/predict",
        json={"features": {"amt": 100.0, "risk": 0.05}},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["prediction"] == 42.0
    assert data["model_version"] == "v1.0.0"
    assert "latency_ms" in data


def test_api_batch_predict(client):
    res = client.post(
        "/api/v1/batch-predict",
        json={"records": [{"amt": 10.0}, {"amt": 20.0}]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 2
    assert len(data["predictions"]) == 2


def test_api_feature_store_write_and_read(client):
    # Write feature
    w_res = client.post(
        "/api/v1/features/write",
        json={"entity_id": "cust_123", "features": {"score": 95.5}},
    )
    assert w_res.status_code == 200

    # Read feature
    r_res = client.get("/api/v1/features/cust_123")
    assert r_res.status_code == 200
    data = r_res.json()
    assert data["feature_values"]["score"] == 95.5


def test_api_cdc_ingestion(client):
    res = client.post(
        "/api/v1/cdc/events",
        json={
            "source": "postgres.orders",
            "entity_id": "ord_555",
            "operation": "INSERT",
            "payload": {"total": 500.0},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["processing_status"] == "PROCESSED"


def test_api_model_health(client):
    res = client.get("/api/v1/models/primary/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded", "critical")
    assert "uptime_seconds" in data
