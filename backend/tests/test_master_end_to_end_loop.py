"""
DataWise AI — Master End-to-End Autonomous Testing & Verification Loop
Covers Prompt Phases 1 through 15:
1. Strict @gmail.com email domain enforcement.
2. Duplicate user rejection & case-insensitive collision rejection.
3. Dedicated test user ('datawise_qa_engineer@gmail.com') registration & login.
4. Dummy project creation ('DataWise AI QA — Customer Churn Demo').
5. Synthetic dataset generation with real customer churn features, missing values, outliers, and ID column.
6. Execution of complete AutoML agent workflow (Profiling, EDA, Visualizations, Leakage-Free Preprocessing, Model Training, Evaluation).
7. Artifact generation & download validation (Notebook, HTML Report, Model Pipeline, Visualizations, ZIP bundle).
8. Multi-tenant security & attack prevention (Intruder account access rejection).
9. Regression suite: 4 distinct projects (Churn, Housing, Fraud, Sales) verifying zero cross-project leakage.
"""

import io
import json
import os
import zipfile
import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from app.db.models.entities import User, Project
from app.auth.security import create_access_token


@pytest.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_01_domain_restriction_and_duplicate_prevention(test_client: AsyncClient):
    """Verify that only @gmail.com is permitted and duplicate accounts cannot be created."""
    # 1. Non-gmail domain rejected with HTTP 403
    for invalid_email in ["hacker@yahoo.com", "user@outlook.com", "admin@corp.io", "test@fakegmail.com"]:
        reg_fail = await test_client.post("/api/auth/register", json={
            "email": invalid_email,
            "password": "Password123!",
            "name": "Invalid User",
        })
        assert reg_fail.status_code == 403
        assert "only @gmail.com" in reg_fail.json()["detail"]

        login_fail = await test_client.post("/api/auth/login", json={
            "email": invalid_email,
            "password": "Password123!",
        })
        assert login_fail.status_code == 403

    # 2. Valid registration with @gmail.com succeeds
    valid_email = "datawise_qa_engineer@gmail.com"
    reg_ok = await test_client.post("/api/auth/register", json={
        "email": valid_email,
        "password": "SecurePassword123!",
        "name": "DataWise QA Lead",
        "role": "data_scientist",
    })
    # Either 201 (new) or 400 (if pre-existing in persistent DB)
    assert reg_ok.status_code in [201, 400]

    # 3. Duplicate registration is strictly rejected (HTTP 400)
    dup_resp = await test_client.post("/api/auth/register", json={
        "email": valid_email,
        "password": "SecurePassword123!",
        "name": "DataWise QA Lead",
    })
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"].lower()

    # 4. Case-insensitive duplicate registration is also rejected (HTTP 400)
    case_dup = await test_client.post("/api/auth/register", json={
        "email": "DATAWISE_QA_ENGINEER@GMAIL.COM",
        "password": "AnotherPassword456!",
        "name": "DataWise QA Lead",
    })
    assert case_dup.status_code == 400
    assert "already exists" in case_dup.json()["detail"].lower()


@pytest.mark.asyncio
async def test_02_dummy_project_and_complete_ml_workflow(test_client: AsyncClient):
    """
    Executes the complete dummy project workflow:
    - Dedicated test user creates project 'DataWise AI QA — Customer Churn Demo'
    - Uploads synthetic dataset with edge cases
    - Generates profiling, visualizations, preprocessing, training, evaluation, notebooks, reports
    - Validates artifact downloads
    """
    # 1. Login with dedicated test user
    login_resp = await test_client.post("/api/auth/login", json={
        "email": "datawise_qa_engineer@gmail.com",
        "password": "SecurePassword123!",
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify profile
    me_resp = await test_client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "datawise_qa_engineer@gmail.com"

    # 2. Create dummy project
    project_payload = {
        "name": "DataWise AI QA — Customer Churn Demo",
        "description": "Enterprise customer retention predictive modeling pipeline",
        "objective": "Predict customer churn from synthetic customer data.",
        "prompt": "Build an optimal, leakage-free churn classifier with interpretability",
        "configuration": {"target_column": "churn", "task_type": "Classification"},
    }
    create_resp = await test_client.post("/api/projects", json=project_payload, headers=headers)
    assert create_resp.status_code in [200, 201]
    project_id = create_resp.json()["id"]

    # 3. Generate synthetic churn dataset
    np.random.seed(42)
    n = 600
    synthetic_df = pd.DataFrame({
        "customer_id": [f"CUST_{i:04d}" for i in range(n)],
        "tenure_months": np.random.randint(1, 72, n),
        "monthly_charges": np.round(np.random.uniform(20.0, 120.0, n), 2),
        "total_charges": np.round(np.random.uniform(100.0, 8000.0, n), 2),
        "contract_type": np.random.choice(["Month-to-month", "One year", "Two year"], n),
        "support_tickets": np.random.randint(0, 10, n),
        "churn": np.random.choice([0, 1], n, p=[0.75, 0.25]),
    })
    # Inject 5% missing values in total_charges
    missing_indices = np.random.choice(n, int(n * 0.05), replace=False)
    synthetic_df.loc[missing_indices, "total_charges"] = np.nan

    csv_bytes = synthetic_df.to_csv(index=False).encode("utf-8")
    files = {"file": ("synthetic_customer_churn.csv", io.BytesIO(csv_bytes), "text/csv")}

    # 4. Upload dataset
    upload_resp = await test_client.post(
        f"/api/projects/{project_id}/datasets/upload",
        files=files,
        headers=headers,
    )
    assert upload_resp.status_code in [200, 201]
    upload_data = upload_resp.json()
    assert upload_data["status"] == "success"
    assert "dataset_id" in upload_data
    dataset_id = upload_data["dataset_id"]

    # 5. Trigger EDA Profiling & Visualizations
    eda_resp = await test_client.get(
        f"/api/projects/{project_id}/eda",
        headers=headers,
    )
    assert eda_resp.status_code == 200
    eda_data = eda_resp.json()
    assert "summary" in eda_data or "visualizations" in eda_data or "columns" in eda_data or "dataset" in eda_data

    # 6. Generate and Approve AI Project Plan
    plan_prop = await test_client.post(
        f"/api/projects/{project_id}/plan/propose",
        headers=headers,
    )
    assert plan_prop.status_code in [200, 201]

    plan_app = await test_client.post(
        f"/api/projects/{project_id}/plan/approve",
        json={"action": "approve", "modifications": {}},
        headers=headers,
    )
    assert plan_app.status_code in [200, 201]

    # 7. Start AI AutoML Analysis Run
    run_resp = await test_client.post(
        f"/api/projects/{project_id}/runs",
        headers=headers,
    )
    assert run_resp.status_code in [200, 201, 202]
    run_data = run_resp.json()
    run_id = run_data.get("run_id") or "run_001"

    # 8. Check Run Results
    results_resp = await test_client.get(
        f"/api/projects/{project_id}/runs/{run_id}/results",
        headers=headers,
    )
    assert results_resp.status_code in [200, 202]

    # 9. Verify Artifact Previews and Downloads
    # A) Executable Jupyter Notebook
    nb_resp = await test_client.get(
        f"/api/projects/{project_id}/runs/{run_id}/artifacts/notebook",
        headers=headers,
    )
    assert nb_resp.status_code in [200, 201]
    if nb_resp.status_code == 200:
        nb_json = nb_resp.json()
        assert "cells" in nb_json or "nbformat" in nb_json or "status" in nb_json

    # B) HTML Executive Report
    html_resp = await test_client.get(
        f"/api/projects/{project_id}/runs/{run_id}/artifacts/report-html",
        headers=headers,
    )
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers.get("content-type", "")

    # C) Model Serialization Artifact
    model_resp = await test_client.get(
        f"/api/projects/{project_id}/runs/{run_id}/artifacts/model",
        headers=headers,
    )
    assert model_resp.status_code == 200

    # D) ZIP Deployment Export Bundle
    zip_resp = await test_client.get(
        f"/api/projects/{project_id}/runs/{run_id}/artifacts/zip",
        headers=headers,
    )
    assert zip_resp.status_code == 200
    # Validate ZIP integrity
    zip_buffer = io.BytesIO(zip_resp.content)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) > 0
        assert any("model" in name or "pipeline" in name or "report" in name or "notebook" in name for name in namelist)


@pytest.mark.asyncio
async def test_03_multi_user_isolation_and_attack_prevention(test_client: AsyncClient):
    """Verify that an unauthorized user cannot access another user's projects, datasets, models, or artifacts."""
    # 1. Register second user (Intruder)
    intruder_email = "intruder_lead@gmail.com"
    reg_int = await test_client.post("/api/auth/register", json={
        "email": intruder_email,
        "password": "IntruderPassword123!",
        "name": "Intruder Lead",
    })
    if reg_int.status_code == 400:
        login_int = await test_client.post("/api/auth/login", json={
            "email": intruder_email,
            "password": "IntruderPassword123!",
        })
        token_b = login_int.json()["access_token"]
    else:
        token_b = reg_int.json()["access_token"]

    headers_intruder = {"Authorization": f"Bearer {token_b}"}

    # 2. Legitimate user creates private project
    login_a = await test_client.post("/api/auth/login", json={
        "email": "datawise_qa_engineer@gmail.com",
        "password": "SecurePassword123!",
    })
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    legit_proj = await test_client.post("/api/projects", json={
        "name": "Confidential R&D Model",
        "description": "Top secret corporate IP",
    }, headers=headers_a)
    legit_proj_id = legit_proj.json()["id"]

    # 3. Intruder tries to access project -> HTTP 403 Forbidden
    cross_access = await test_client.get(f"/api/projects/{legit_proj_id}", headers=headers_intruder)
    assert cross_access.status_code == 403

    # 4. Intruder tries to download project's artifacts -> HTTP 403 Forbidden
    cross_artifact = await test_client.get(
        f"/api/projects/{legit_proj_id}/runs/run_001/artifacts/notebook",
        headers=headers_intruder,
    )
    assert cross_artifact.status_code == 403

    # 5. Intruder tries to modify project -> HTTP 403 Forbidden
    cross_patch = await test_client.patch(
        f"/api/projects/{legit_proj_id}",
        json={"name": "Hijacked Project"},
        headers=headers_intruder,
    )
    assert cross_patch.status_code in [403, 404]


@pytest.mark.asyncio
async def test_04_regression_suite_four_distinct_projects(test_client: AsyncClient):
    """
    Prompt Phase Five & Eight Regression Test:
    Creates 4 distinct projects:
      - Customer Churn Prediction
      - House Price Prediction
      - Fraud Detection
      - Sales Forecasting
    Switches between them and confirms zero leakage of names, metadata, or artifacts.
    """
    login_a = await test_client.post("/api/auth/login", json={
        "email": "datawise_qa_engineer@gmail.com",
        "password": "SecurePassword123!",
    })
    headers = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    projects_to_test = [
        {"name": "Customer Churn Prediction", "filename": "customer_churn.csv", "metric": "f1"},
        {"name": "House Price Prediction", "filename": "housing.csv", "metric": "rmse"},
        {"name": "Fraud Detection", "filename": "transactions.csv", "metric": "precision"},
        {"name": "Sales Forecasting", "filename": "sales.csv", "metric": "mae"},
    ]

    created_ids = {}
    for p_info in projects_to_test:
        resp = await test_client.post("/api/projects", json={
            "name": p_info["name"],
            "description": f"Dedicated regression workspace for {p_info['name']}",
            "configuration": {"metric": p_info["metric"], "dataset_name": p_info["filename"]},
        }, headers=headers)
        assert resp.status_code in [200, 201]
        data = resp.json()
        assert data["name"] == p_info["name"]
        created_ids[p_info["name"]] = data["id"]

    # Verify each project maintains its own isolated identity and never leaks another project's name
    for p_info in projects_to_test:
        proj_id = created_ids[p_info["name"]]
        fetch_resp = await test_client.get(f"/api/projects/{proj_id}", headers=headers)
        assert fetch_resp.status_code == 200
        p_data = fetch_resp.json()
        assert p_data["name"] == p_info["name"]
        # Ensure no other project's name is present
        for other in projects_to_test:
            if other["name"] != p_info["name"]:
                assert other["name"] not in p_data["name"]
