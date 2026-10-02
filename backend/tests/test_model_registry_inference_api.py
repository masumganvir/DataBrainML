"""
DataWise AI — Model Registry & Dynamic Serving API Test Suite (Phases 11 & 12)
Validates model registration, versioning, status transitions, and prediction inference.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_model_registry_and_inference_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a model
        reg_payload = {
            "project_id": "test_project_alpha",
            "model_name": "RandomForestClassifier",
            "version": "v1.0.0",
            "task_type": "classification",
            "target_column": "churn",
            "feature_columns": ["age", "tenure", "monthly_charges"],
            "metrics": {"f1_score": 0.892, "roc_auc": 0.941},
        }
        res = await client.post("/api/models/register", json=reg_payload)
        assert res.status_code == 200, res.text
        data = res.json()
        model_id = data["model_id"]
        assert data["record"]["status"] == "development"

        # 2. List models
        list_res = await client.get("/api/models")
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1

        # 3. Transition status from development -> staging -> production
        trans_res = await client.post(
            f"/api/models/{model_id}/transition",
            json={"target_status": "production", "reason": "Passed automated validation pipeline"},
        )
        assert trans_res.status_code == 200
        assert trans_res.json()["new_status"] == "production"

        # 4. Check model health and info
        health_res = await client.get(f"/api/models/{model_id}/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"

        info_res = await client.get(f"/api/models/{model_id}/info")
        assert info_res.status_code == 200
        assert info_res.json()["model_name"] == "RandomForestClassifier"

        # 5. Check schema endpoint
        schema_res = await client.get(f"/api/models/{model_id}/schema")
        assert schema_res.status_code == 200
        assert "input_schema" in schema_res.json()

        # 6. Execute single prediction
        pred_res = await client.post(
            f"/api/models/{model_id}/predict",
            json={"features": {"age": 45, "tenure": 12, "monthly_charges": 65.5}},
        )
        assert pred_res.status_code == 200
        pred_data = pred_res.json()
        assert "prediction" in pred_data
        assert pred_data["latency_ms"] >= 0

        # 7. Execute batch prediction
        batch_res = await client.post(
            f"/api/models/{model_id}/predict/batch",
            json={
                "records": [
                    {"age": 25, "tenure": 2, "monthly_charges": 29.99},
                    {"age": 60, "tenure": 48, "monthly_charges": 99.50},
                ]
            },
        )
        assert batch_res.status_code == 200
        batch_data = batch_res.json()
        assert batch_data["total_records"] == 2
        assert len(batch_data["predictions"]) == 2
