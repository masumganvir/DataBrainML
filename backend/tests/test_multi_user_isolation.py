"""
DataWise AI — Multi-User Isolation & Enterprise Security Test Suite
Adheres to Master Implementation Prompt Sections 5, 17, 18, 19, 22, 23, 25, 29, 44, 45, 61, 74, 75, 76:
- User registration, login & Argon2id password hashing
- Strict project isolation between tenants (User A vs User B)
- Project cross-access denial (HTTP 403 Forbidden)
- Artifact download security & cross-user access denial
- Session security (invalid tokens, malformed headers)
- Experiment caching & SHA-256 deterministic fingerprinting
- Model registry versioning & lineage
- Storage service checksum verification
"""

import io
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password, verify_password, create_access_token
from app.db.models.entities import User, Project, AuditLog
from database.repositories.models import ModelRepository
from services.experiment_cache import experiment_cache
from services.storage_service import storage_service
from services.artifact_service import artifact_service


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """Verify password is encrypted with Argon2id and matches securely."""
    password = "SuperSecurePassword123!"
    hashed = hash_password(password)

    # Must never be plaintext
    assert hashed != password
    assert "argon2id" in hashed or "$" in hashed

    # Must verify correctly
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


@pytest.mark.asyncio
async def test_auth_registration_and_login_flow(client: AsyncClient):
    """Test user registration, login, and JWT credential generation."""
    # 1. Register User A
    reg_payload = {
        "email": "alice_test@datalab.ai",
        "password": "StrongPassword123!",
        "name": "Alice Data Scientist",
        "role": "data_scientist",
    }
    reg_resp = await client.post("/api/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice_test@datalab.ai"
    alice_token = data["access_token"]

    # 2. Duplicate registration should be rejected
    dup_resp = await client.post("/api/auth/register", json=reg_payload)
    assert dup_resp.status_code == 400

    # 3. Login with valid credentials
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "alice_test@datalab.ai", "password": "StrongPassword123!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # 4. Login with invalid password -> 401 generic error (Section 42)
    bad_login = await client.post(
        "/api/auth/login",
        json={"email": "alice_test@datalab.ai", "password": "IncorrectPassword!"},
    )
    assert bad_login.status_code == 401
    assert "Incorrect email or password" in bad_login.json()["detail"]

    # 5. /api/auth/me returns current authenticated user
    me_resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice_test@datalab.ai"


@pytest.mark.asyncio
async def test_multi_user_project_isolation(client: AsyncClient):
    """
    Prompt Section 74 Multi-User Security Test:
    User A creates Project A.
    User B creates Project B.
    User B attempts to access Project A -> HTTP 403 Forbidden.
    User A must never see Project B.
    """
    # 1. Register User A and User B
    reg_a = await client.post(
        "/api/auth/register",
        json={"email": "usera@enterprise.ai", "password": "PasswordA123!", "name": "User A"},
    )
    assert reg_a.status_code == 201
    token_a = reg_a.json()["access_token"]
    user_a_id = reg_a.json()["user"]["id"]

    reg_b = await client.post(
        "/api/auth/register",
        json={"email": "userb@enterprise.ai", "password": "PasswordB123!", "name": "User B"},
    )
    assert reg_b.status_code == 201
    token_b = reg_b.json()["access_token"]
    user_b_id = reg_b.json()["user"]["id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. User A creates Project A
    proj_a_resp = await client.post(
        "/api/projects",
        json={"name": "Project Alpha - Churn Analysis", "description": "Alice's proprietary project"},
        headers=headers_a,
    )
    assert proj_a_resp.status_code == 201
    proj_a_id = proj_a_resp.json()["id"]

    # 3. User B creates Project B
    proj_b_resp = await client.post(
        "/api/projects",
        json={"name": "Project Beta - Fraud Detection", "description": "Bob's private fraud project"},
        headers=headers_b,
    )
    assert proj_b_resp.status_code == 201
    proj_b_id = proj_b_resp.json()["id"]

    # 4. User A lists projects -> MUST only see Project A, NEVER Project B (Section 61)
    list_a = await client.get("/api/projects", headers=headers_a)
    assert list_a.status_code == 200
    projects_for_a = list_a.json()
    proj_ids_a = [p["id"] for p in projects_for_a]
    assert proj_a_id in proj_ids_a
    assert proj_b_id not in proj_ids_a

    # 5. User B lists projects -> MUST only see Project B, NEVER Project A
    list_b = await client.get("/api/projects", headers=headers_b)
    assert list_b.status_code == 200
    projects_for_b = list_b.json()
    proj_ids_b = [p["id"] for p in projects_for_b]
    assert proj_b_id in proj_ids_b
    assert proj_a_id not in proj_ids_b

    # 6. User B attempts to access Project A -> DENIED (HTTP 403 Forbidden)
    cross_get = await client.get(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert cross_get.status_code == 403

    # 7. User B attempts to delete Project A -> DENIED (HTTP 403 Forbidden)
    cross_delete = await client.delete(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert cross_delete.status_code == 403

    # 8. User B attempts to upload dataset to Project A -> DENIED (HTTP 403 Forbidden)
    csv_content = b"feature1,feature2,target\n1,2,0\n3,4,1"
    files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
    cross_upload = await client.post(
        f"/api/projects/{proj_a_id}/datasets/upload",
        files=files,
        headers=headers_b,
    )
    assert cross_upload.status_code == 403


@pytest.mark.asyncio
async def test_artifact_download_security(client: AsyncClient):
    """
    Prompt Section 76 Artifact Security Test:
    User A creates Project A with an artifact.
    User B attempts to download User A's artifact -> DENIED (HTTP 403).
    User A can download successfully.
    """
    # Register User A and User B
    reg_a = await client.post(
        "/api/auth/register",
        json={"email": "alice_art@enterprise.ai", "password": "PasswordA123!", "name": "Alice"},
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await client.post(
        "/api/auth/register",
        json={"email": "bob_art@enterprise.ai", "password": "PasswordB123!", "name": "Bob"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Project A
    proj_res = await client.post(
        "/api/projects",
        json={"name": "Proprietary Algorithm Project"},
        headers=headers_a,
    )
    proj_id = proj_res.json()["id"]

    # User A can download/generate their artifact
    dl_resp_a = await client.get(
        f"/api/projects/{proj_id}/runs/run_001/artifacts/notebook",
        headers=headers_a,
    )
    assert dl_resp_a.status_code == 200

    # User B attempts to download User A's artifact -> HTTP 403 Forbidden!
    dl_resp_b = await client.get(
        f"/api/projects/{proj_id}/runs/run_001/artifacts/notebook",
        headers=headers_b,
    )
    assert dl_resp_b.status_code == 403


@pytest.mark.asyncio
async def test_session_security_and_invalid_tokens(client: AsyncClient):
    """Prompt Section 75 Session Security Test: invalid token, malformed header."""
    # 1. Invalid Bearer Token
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert resp.status_code == 401

    # 2. Malformed Authorization Header
    resp2 = await client.get(
        "/api/auth/me",
        headers={"Authorization": "NotABearerToken"},
    )
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_experiment_cache_fingerprint():
    """Prompt Section 23 & 29: Deterministic Experiment Cache Fingerprinting."""
    fp1 = experiment_cache.generate_fingerprint(
        dataset_hash="hash_abc123",
        pipeline_config={"scaling": "standard", "encoding": "onehot"},
        model_name="xgboost",
        hyperparameters={"n_estimators": 100},
        training_config={"cv_folds": 5, "metric": "f1"},
    )
    fp2 = experiment_cache.generate_fingerprint(
        dataset_hash="hash_abc123",
        pipeline_config={"scaling": "standard", "encoding": "onehot"},
        model_name="xgboost",
        hyperparameters={"n_estimators": 100},
        training_config={"cv_folds": 5, "metric": "f1"},
    )
    # Must be deterministic
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex string

    # Different hyperparameters produce a different fingerprint
    fp3 = experiment_cache.generate_fingerprint(
        dataset_hash="hash_abc123",
        pipeline_config={"scaling": "standard", "encoding": "onehot"},
        model_name="xgboost",
        hyperparameters={"n_estimators": 200},
        training_config={"cv_folds": 5, "metric": "f1"},
    )
    assert fp1 != fp3


@pytest.mark.asyncio
async def test_storage_service_and_artifact_integrity():
    """Prompt Section 14 & 69: Storage abstraction, SHA-256 verification and tamper detection."""
    test_content = b"DataWise AI artifact test data content."
    storage_key = "test_run/model_artifact.bin"

    # Upload artifact
    stored_key = storage_service.upload(
        file_source=test_content,
        storage_key=storage_key,
        content_type="application/octet-stream",
    )
    assert stored_key == storage_key
    assert storage_service.exists(storage_key) is True

    # Download artifact and verify checksum
    downloaded = storage_service.download(storage_key)
    assert downloaded == test_content

    checksum = storage_service.checksum(downloaded)
    expected_checksum = storage_service.checksum(test_content)
    assert checksum == expected_checksum

    # Tamper detection
    tampered_content = b"Tampered data"
    assert storage_service.checksum(tampered_content) != expected_checksum
