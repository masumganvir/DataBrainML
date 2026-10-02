"""DataWise AI — Authentication, RBAC & Audit Tests."""

import pytest
from app.auth.security import (
    hash_password,
    verify_password,
    generate_api_key,
    hash_api_key,
    create_access_token,
    decode_access_token,
)
from app.auth.rbac import ROLE_PERMISSIONS
from app.audit.logger import AuditLogger
from app.db.session import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


def test_password_hashing():

    pw = "SuperSecret#2026!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_api_key_generation_and_hashing():
    raw_key, prefix, key_hash = generate_api_key()
    assert raw_key.startswith("dw_live_")
    assert raw_key.startswith(prefix)
    assert hash_api_key(raw_key) == key_hash


def test_jwt_token_creation_and_decoding():
    payload = {"sub": "user_uuid_123", "role": "data_scientist"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_uuid_123"
    assert decoded["role"] == "data_scientist"


def test_rbac_matrix():
    assert "model.promote" in ROLE_PERMISSIONS["owner"]
    assert "model.promote" in ROLE_PERMISSIONS["data_scientist"]
    assert "model.promote" not in ROLE_PERMISSIONS["viewer"]
    assert "dataset.read" in ROLE_PERMISSIONS["viewer"]


@pytest.mark.asyncio
async def test_audit_logger():
    audit_id = await AuditLogger.log(
        action="dataset_upload",
        resource_type="dataset",
        resource_id="ds_123",
        user_id="user_test",
        metadata={"filename": "customers.csv", "rows": 1200},
    )
    assert audit_id is not None
