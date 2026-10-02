"""
DataWise AI — End-to-End API Integration Test with TestClient
Validates:
- Project creation via /api/projects
- Triggering real ML run via /api/projects/{id}/runs
- Completion and verification of genuine results
- Artifact downloads (/artifacts/notebook, /artifacts/html, /artifacts/model, /artifacts/bundle)
- Live inference via /api/projects/{id}/predict
"""

import time
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_e2e_projects_pipeline_and_prediction(client):
    # 1. Create Project
    res = client.post(
        "/api/projects",
        json={
            "name": "E2E Churn Test Workbench",
            "prompt": "Predict customer churn using realistic tree models.",
            "configuration": {
                "target_column": "churn",
                "task_type": "Classification",
                "auto_approve_outliers": True,
            },
        },
    )
    assert res.status_code == 201
    proj_data = res.json()
    project_id = proj_data["id"]
    assert project_id.startswith("proj_")

    # 2. Trigger Run
    run_res = client.post(
        f"/api/projects/{project_id}/runs",
        json={"prompt": "Train champion model on customer churn."},
    )
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]
    assert run_id.startswith("run_")

    # 3. Poll for pipeline completion
    completed = False
    for _ in range(40):
        time.sleep(0.5)
        st_res = client.get(f"/api/projects/{project_id}/runs/{run_id}")
        assert st_res.status_code == 200
        st_data = st_res.json()
        if st_data.get("status") == "COMPLETED":
            completed = True
            break
        if st_data.get("status") == "PAUSED":
            # Auto-approve if paused
            client.post(
                f"/api/projects/{project_id}/runs/{run_id}/decisions",
                json={"decision_key": "outlier", "decision_value": "Cap", "rationale": "Auto approval"},
            )

    assert completed is True, "Pipeline did not reach COMPLETED status within timeout"

    # 4. Verify Results
    results_res = client.get(f"/api/projects/{project_id}/runs/{run_id}/results")
    assert results_res.status_code == 200
    results = results_res.json()
    assert results["best_model"] is not None
    assert results["primary_metric_value"] > 0
    assert results["generalization_health"] in ["Healthy", "Warning: Moderate Overfitting", "Warning: Underfitting"]
    assert len(results["model_comparison"]) >= 2

    # 5. Verify Artifact Downloads
    for art in ["notebook", "html", "summary", "model", "pipeline", "bundle"]:
        art_res = client.get(f"/api/projects/{project_id}/runs/{run_id}/artifacts/{art}")
        assert art_res.status_code == 200
        assert len(art_res.content) > 0

    # 6. Test Prediction Endpoint (/api/projects/{project_id}/predict)
    schema_res = client.get(f"/api/projects/{project_id}/predict/schema")
    assert schema_res.status_code == 200
    col_schema = schema_res.json()["column_schema"]
    assert len(col_schema) > 0

    sample_features = {c["name"]: c.get("example", 0) for c in col_schema}
    pred_res = client.post(
        f"/api/projects/{project_id}/predict",
        json={"features": sample_features},
    )
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert "prediction" in pred_data
    assert "latency_ms" in pred_data
    assert pred_data["latency_ms"] >= 0
    assert "confidence" in pred_data
    print(f"\n[E2E TEST PASSED] Prediction: {pred_data['prediction']} | Model: {pred_data.get('model')}")
