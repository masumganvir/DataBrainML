"""
DataWise AI — STEP 1 Tests: Core Infrastructure

Tests:
  - Settings load without errors
  - Database tables are created
  - Health endpoint responds correctly
  - Sessions CRUD works end-to-end
"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ #
#  Settings Tests
# ------------------------------------------------------------------ #

class TestSettings:
    def test_settings_load(self):
        """Settings should load with default values."""
        from app.config.settings import get_settings
        settings = get_settings()
        assert settings is not None
        assert settings.app_env in ("development", "production", "testing")
        assert settings.llm_provider in ("gemini", "openai")

    def test_allowed_extensions_set(self):
        from app.config.settings import get_settings
        settings = get_settings()
        exts = settings.allowed_extensions_set
        assert "csv" in exts
        assert "xlsx" in exts
        assert "xls" in exts
        assert "json" in exts

    def test_max_upload_size_bytes(self):
        from app.config.settings import get_settings
        settings = get_settings()
        # Default 100 MB
        assert settings.max_upload_size_bytes == 100 * 1024 * 1024

    def test_cors_origins_list(self):
        from app.config.settings import get_settings
        settings = get_settings()
        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) >= 1


# ------------------------------------------------------------------ #
#  Database Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestDatabase:
    async def test_db_tables_created(self, db_engine):
        """Database tables should be created by the test fixture."""
        from sqlalchemy import inspect, text
        async with db_engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        assert "sessions" in tables
        assert "datasets" in tables
        assert "conversation_messages" in tables
        assert "artifacts" in tables
        assert "user_decisions" in tables


# ------------------------------------------------------------------ #
#  Health Endpoint Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestHealthEndpoints:
    async def test_root_health(self, client):
        """Root /health should return 200 with ok status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "DataWise AI"

    async def test_api_health(self, client):
        """API /api/health should return 200 with llm_provider."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "llm_provider" in data


# ------------------------------------------------------------------ #
#  Sessions CRUD Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestSessionsCRUD:
    async def test_create_session_default_name(self, client):
        """Creating a session without a name should use 'Untitled Session'."""
        response = await client.post("/api/sessions", json={})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Untitled Session"
        assert data["status"] == "created"
        assert data["current_stage"] == "INGEST"
        assert "id" in data

    async def test_create_session_custom_name(self, client):
        """Creating a session with a name should persist that name."""
        response = await client.post("/api/sessions", json={"name": "My Test Analysis"})
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Analysis"

    async def test_list_sessions_empty(self, client):
        """Listing sessions on fresh DB should return empty list."""
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_sessions_after_create(self, client):
        """Listing sessions should return created sessions."""
        await client.post("/api/sessions", json={"name": "Session A"})
        await client.post("/api/sessions", json={"name": "Session B"})
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_session_by_id(self, client):
        """Getting a session by ID should return the correct session."""
        create_resp = await client.post("/api/sessions", json={"name": "Test"})
        session_id = create_resp.json()["id"]
        get_resp = await client.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == session_id

    async def test_get_session_not_found(self, client):
        """Getting a non-existent session should return 404."""
        response = await client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404

    async def test_update_session_name(self, client):
        """Updating session name should persist the change."""
        create_resp = await client.post("/api/sessions", json={"name": "Old Name"})
        session_id = create_resp.json()["id"]
        update_resp = await client.patch(
            f"/api/sessions/{session_id}", json={"name": "New Name"}
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "New Name"

    async def test_delete_session(self, client):
        """Deleting a session should remove it from the database."""
        create_resp = await client.post("/api/sessions", json={"name": "To Delete"})
        session_id = create_resp.json()["id"]
        del_resp = await client.delete(f"/api/sessions/{session_id}")
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/sessions/{session_id}")
        assert get_resp.status_code == 404


# ------------------------------------------------------------------ #
#  State Schema Tests
# ------------------------------------------------------------------ #

class TestDataScienceState:
    def test_state_import(self):
        """DataScienceState TypedDict should import without errors."""
        from app.state.data_science_state import DataScienceState, ColumnInfo, MissingValueReport
        assert DataScienceState is not None
        assert ColumnInfo is not None
        assert MissingValueReport is not None

    def test_state_fields_exist(self):
        """All required fields should be defined on the TypedDict."""
        from app.state.data_science_state import DataScienceState
        annotations = DataScienceState.__annotations__
        required_fields = [
            "session_id", "dataset_id", "dataset_path_original",
            "numerical_columns", "categorical_columns", "target_column",
            "missing_value_report", "outlier_report", "conversation_history",
            "current_stage", "errors", "pipeline_definition",
        ]
        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"
