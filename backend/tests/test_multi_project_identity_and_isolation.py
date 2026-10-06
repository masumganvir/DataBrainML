import pytest
import io
import hashlib
from httpx import AsyncClient, ASGITransport
from main import app
from app.auth.security import create_access_token
from app.storage.service import storage_service
from app.agents.system_agents import system_improvement_agent, system_testing_agent

def get_auth_header(user_id: str, email: str = "test@example.com"):
    token = create_access_token(data={"sub": user_id, "email": email, "role": "data_scientist"})
    return {
        "Authorization": f"Bearer {token}",
        "X-User-Id": user_id,
        "X-User-Email": email,
    }

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_project_identity_and_slug_generation(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 4 & 5:
    Every project must have: project_id, project_slug, project_name, description,
    objective, created_by, created_at, updated_at, status, visibility, metadata.
    Slug must be unique based on project-name + short unique identifier.
    """
    headers = get_auth_header("user_alpha_1", "alpha1@datalab.ai")
    payload = {
        "name": "House Price Prediction",
        "description": "Predict residential home values based on location and specs",
        "objective": "Minimize Root Mean Squared Error (RMSE) on house valuation",
        "configuration": {"task_type": "Regression", "target_column": "price"}
    }
    response = await async_client.post("/api/projects", json=payload, headers=headers)
    assert response.status_code in [200, 201], response.text
    data = response.json()

    assert "id" in data
    assert "slug" in data
    assert "house-price-prediction" in data["slug"]
    assert data["name"] == "House Price Prediction"
    assert data["objective"] == payload["objective"]
    assert "Customer Churn" not in data["name"]
    assert "churn" not in data["slug"]

    # Verify lookups by ID and by Slug
    proj_id = data["id"]
    slug = data["slug"]

    get_by_id = await async_client.get(f"/api/projects/{proj_id}", headers=headers)
    assert get_by_id.status_code == 200
    assert get_by_id.json()["id"] == proj_id

    get_by_slug = await async_client.get(f"/api/projects/{slug}", headers=headers)
    assert get_by_slug.status_code == 200
    assert get_by_slug.json()["id"] == proj_id

@pytest.mark.asyncio
async def test_multi_user_and_cross_project_isolation(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 12, 34, 47:
    User A cannot access User B's project or artifacts. Direct API requests
    for unauthorized projects must return 404 or 403.
    """
    user_a = get_auth_header("user_alice_test", "alice@datalab.ai")
    user_b = get_auth_header("user_bob_test", "bob@datalab.ai")

    # Alice creates Project A
    res_a = await async_client.post("/api/projects", json={
        "name": "Alice Private Project",
        "description": "Confidential medical records",
        "objective": "Clinical outcome forecasting"
    }, headers=user_a)
    assert res_a.status_code in [200, 201]
    proj_a_id = res_a.json()["id"]

    # Bob attempts to fetch Alice's Project A
    res_bob_fetch = await async_client.get(f"/api/projects/{proj_a_id}", headers=user_b)
    # Must return 404 or 403 and never reveal Alice's data
    assert res_bob_fetch.status_code in [403, 404]

    # Bob attempts to update Alice's Project A
    res_bob_update = await async_client.patch(f"/api/projects/{proj_a_id}", json={
        "name": "Hacked Name"
    }, headers=user_b)
    assert res_bob_update.status_code in [403, 404]

@pytest.mark.asyncio
async def test_dynamic_project_naming_regression_no_churn_leakage(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 3, 48, 70:
    Regression test for old project name leakage bug:
    Creating "House Price Prediction" or "Credit Card Fraud Detection"
    must NEVER return or leak "Customer Churn Prediction".
    """
    headers = get_auth_header("user_audit_1", "audit1@datalab.ai")

    # Project 1: House Price Prediction
    p1_res = await async_client.post("/api/projects", json={
        "name": "House Price Prediction",
        "description": "Real estate appraisal regression",
        "objective": "Predict sale price in dollars"
    }, headers=headers)
    assert p1_res.status_code in [200, 201]
    p1 = p1_res.json()

    assert p1["name"] == "House Price Prediction"
    assert "Customer Churn" not in p1["name"]

    # Project 2: Credit Card Fraud Detection
    p2_res = await async_client.post("/api/projects", json={
        "name": "Credit Card Fraud Detection",
        "description": "Anomaly detection on payment card swipes",
        "objective": "Identify stolen cards with high precision"
    }, headers=headers)
    assert p2_res.status_code in [200, 201]
    p2 = p2_res.json()

    assert p2["name"] == "Credit Card Fraud Detection"
    assert "Customer Churn" not in p2["name"]
    assert "House Price" not in p2["name"]

    # Listing projects for user returns both with strictly distinct names
    list_res = await async_client.get("/api/projects", headers=headers)
    assert list_res.status_code == 200
    names = [p["name"] for p in list_res.json()]
    assert "House Price Prediction" in names
    assert "Credit Card Fraud Detection" in names
    # Verify no random default fallback injected
    assert "Customer Churn Intelligence" not in names

@pytest.mark.asyncio
async def test_dataset_sha256_duplicate_detection(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 8:
    Calculate SHA-256 hash of uploaded files. If identical file is uploaded
    again with force=False, detect duplicate and warn user with options.
    """
    headers = get_auth_header("user_hash_1", "hash1@datalab.ai")
    create_res = await async_client.post("/api/projects", json={
        "name": "Duplicate Detection Workspace"
    }, headers=headers)
    assert create_res.status_code in [200, 201]
    proj_id = create_res.json()["id"]

    csv_content = b"col1,col2,target\n1,2,0\n3,4,1\n5,6,0\n"
    expected_hash = hashlib.sha256(csv_content).hexdigest()

    # First upload
    file1 = ("test_data.csv", io.BytesIO(csv_content), "text/csv")
    res1 = await async_client.post(
        f"/api/projects/{proj_id}/datasets/upload",
        files={"file": file1},
        data={"force": "false"},
        headers=headers
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1.get("duplicate") is not True
    assert d1.get("file_hash") == expected_hash

    # Second upload of identical file without force
    file2 = ("test_data.csv", io.BytesIO(csv_content), "text/csv")
    res2 = await async_client.post(
        f"/api/projects/{proj_id}/datasets/upload",
        files={"file": file2},
        data={"force": "false"},
        headers=headers
    )
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2.get("duplicate") is True
    assert d2.get("file_hash") == expected_hash
    assert "already exists" in d2.get("message", "").lower()

def test_storage_namespacing():
    """
    MASTER PROMPT SECTION 6 & 32:
    Storage service must strictly namespace files by users/{user_id}/projects/{project_id}/{category}/.
    """
    user_id = "usr_9988"
    project_id = "proj_7766"

    key = storage_service.build_project_key(
        user_id=user_id,
        project_id=project_id,
        category="models",
        filename="champion_model.joblib"
    )

    expected_prefix = f"users/{user_id}/projects/{project_id}/models/"
    assert key.startswith(expected_prefix)
    assert "champion_model" in key
    assert key.endswith(".joblib")

@pytest.mark.asyncio
async def test_ai_project_planner_agent_proposal_and_approval(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 19 & 20:
    AI Project Planner Agent analyzes dataset profile & user prompt,
    generates proposal, and requires human approval before starting main pipeline.
    """
    headers = get_auth_header("user_planner_1", "planner1@datalab.ai")
    create_res = await async_client.post("/api/projects", json={
        "name": "Pending Approval Project"
    }, headers=headers)
    assert create_res.status_code in [200, 201]
    proj_id = create_res.json()["id"]

    # Propose plan
    prop_res = await async_client.post(f"/api/projects/{proj_id}/plan/propose", json={
        "prompt": "We want to forecast monthly sales for 50 retail store locations.",
        "dataset_profile": {"columns": ["store_id", "month", "promotions", "sales"], "target_candidate": "sales"},
        "custom_name": "Retail Store Sales Forecast"
    }, headers=headers)
    assert prop_res.status_code == 200
    proposal = prop_res.json()["proposal"]

    assert proposal["task_type"] in ["regression", "time_series"]
    assert proposal["target_candidate"] == "sales"
    assert proposal["project_name"] == "Retail Store Sales Forecast"
    assert "recommended_pipeline" in proposal

    # Human Approval
    app_res = await async_client.post(f"/api/projects/{proj_id}/plan/approve", json={
        "proposal": proposal
    }, headers=headers)
    assert app_res.status_code == 200
    approved_proj = app_res.json()["project"]
    assert approved_proj["name"] == "Retail Store Sales Forecast"

@pytest.mark.asyncio
async def test_project_prompt_versioning(async_client: AsyncClient):
    """
    MASTER PROMPT SECTION 23:
    Every project prompt must support versioning (v1, v2, etc.).
    Historical prompts must never be destroyed.
    """
    headers = get_auth_header("user_prompt_1", "prompt1@datalab.ai")
    create_res = await async_client.post("/api/projects", json={
        "name": "Versioned Prompts Project",
        "prompt": "Initial prompt v1: Baseline accuracy focus"
    }, headers=headers)
    assert create_res.status_code in [200, 201]
    proj_id = create_res.json()["id"]

    # Add prompt v2
    v2_res = await async_client.post(f"/api/projects/{proj_id}/prompts", json={
        "content": "Updated prompt v2: Maximize precision and recall balance"
    }, headers=headers)
    assert v2_res.status_code in [200, 201]
    v2_data = v2_res.json()
    assert v2_data["version"] >= 2

    # Get prompt history
    hist_res = await async_client.get(f"/api/projects/{proj_id}/prompts", headers=headers)
    assert hist_res.status_code == 200
    prompts = hist_res.json()
    assert len(prompts) >= 2
    contents = [p["content"] for p in prompts]
    assert any("v1" in c for c in contents)
    assert any("v2" in c for c in contents)

@pytest.mark.asyncio
async def test_system_improvement_and_testing_agents():
    """
    MASTER PROMPT SECTION 44 & 46:
    System Improvement Agent & System Testing Agent diagnostics.
    """
    improvements = await system_improvement_agent.analyze_system_health()
    assert isinstance(improvements, list)
    assert len(improvements) > 0
    assert "recommendation" in improvements[0]
    assert "priority" in improvements[0]

    diagnostics = await system_testing_agent.run_diagnostics()
    assert diagnostics["overall_status"] == "HEALTHY"
    assert "tests" in diagnostics
    assert len(diagnostics["tests"]) >= 5
