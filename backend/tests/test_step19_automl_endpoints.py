"""
DataWise AI — STEP 19 Tests: Advanced AutoML Endpoints & Deliverables

Tests:
  - Setting domain, objective, and execution mode (POST /context)
  - Leak-free candidate model training and CV evaluation (POST /ml/train)
  - Interactive model comparison dashboard (GET /ml/comparison)
  - Champion model manual override (POST /ml/select-model)
  - 24-section Jupyter Notebook generation & download (POST/GET /notebook)
  - Artifacts packaging, ZIP bundle, and model download (POST/GET /artifacts)
"""

from __future__ import annotations

import io
import json
import zipfile
import pytest
import pandas as pd


@pytest.mark.asyncio
class TestAutoMLEndpoints:

    async def _setup_session_with_data(self, client):
        # 1. Create session
        create_resp = await client.post("/api/sessions", json={"name": "AutoML Test Session"})
        assert create_resp.status_code == 201
        session_id = create_resp.json()["id"]

        # 2. Upload dataset with mixed types & target
        df = pd.DataFrame({
            "age": [25, 38, 45, 29, 52, 41, 60, 31, 22, 49, 34, 58],
            "income": [45000.0, 72000.0, 95000.0, 51000.0, 110000.0, 88000.0, 130000.0, 62000.0, 39000.0, 102000.0, 70000.0, 125000.0],
            "department": ["Sales", "Engineering", "Engineering", "Marketing", "Sales", "Management", "Management", "Sales", "Support", "Engineering", "Marketing", "Sales"],
            "is_churn": [0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1],
        })
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        files = {"file": ("employee_churn.csv", io.BytesIO(csv_bytes), "text/csv")}
        upload_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        assert upload_resp.status_code == 201

        return session_id

    async def test_update_session_context(self, client):
        session_id = await self._setup_session_with_data(client)

        resp = await client.post(
            f"/api/sessions/{session_id}/context",
            json={
                "dataset_domain": "human_resources",
                "prediction_objective": "employee_churn",
                "execution_mode": "guided",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_domain"] == "human_resources"
        assert data["prediction_objective"] == "employee_churn"
        assert data["execution_mode"] == "guided"

    async def test_train_models_and_comparison(self, client):
        session_id = await self._setup_session_with_data(client)

        # 1. Train models
        train_resp = await client.post(
            f"/api/sessions/{session_id}/ml/train",
            json={
                "target_column": "is_churn",
                "task_type": "classification",
                "cv_folds": 2,
            },
        )
        assert train_resp.status_code == 200
        train_data = train_resp.json()

        assert train_data["task_type"] == "classification"
        assert train_data["target_column"] == "is_churn"
        assert len(train_data["models"]) >= 2
        assert train_data["selected_final_model"] is not None
        assert "production_readiness" in train_data
        assert train_data["production_readiness"]["status"] in ("PASS", "WARNING")

        # 2. Get comparison dashboard
        comp_resp = await client.get(f"/api/sessions/{session_id}/ml/comparison")
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert comp_data["trained"] is True
        assert len(comp_data["models"]) >= 2

        # Verify champion is flagged
        champion = next((m for m in comp_data["models"] if m.get("is_champion")), None)
        assert champion is not None
        assert champion["model_name"] == train_data["selected_final_model"]

    async def test_select_champion_model_override(self, client):
        session_id = await self._setup_session_with_data(client)

        # Train first
        await client.post(
            f"/api/sessions/{session_id}/ml/train",
            json={"target_column": "is_churn", "task_type": "classification", "cv_folds": 2},
        )

        comp_resp = await client.get(f"/api/sessions/{session_id}/ml/comparison")
        models = comp_resp.json()["models"]
        first_model_name = models[0]["model_name"]

        # Override champion
        select_resp = await client.post(
            f"/api/sessions/{session_id}/ml/select-model",
            json={
                "model_name": first_model_name,
                "rationale": "High business interpretability requirement",
            },
        )
        assert select_resp.status_code == 200
        select_data = select_resp.json()
        assert select_data["selected_final_model"] == first_model_name

    async def test_generate_and_download_notebook(self, client):
        session_id = await self._setup_session_with_data(client)

        # Train first
        await client.post(
            f"/api/sessions/{session_id}/ml/train",
            json={"target_column": "is_churn", "task_type": "classification", "cv_folds": 2},
        )

        # 1. Generate notebook
        gen_resp = await client.post(f"/api/sessions/{session_id}/notebook/generate")
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert "notebook_path" in gen_data
        assert gen_data["filename"].endswith(".ipynb")

        # 2. Download notebook
        dl_resp = await client.get(f"/api/sessions/{session_id}/notebook/download")
        assert dl_resp.status_code == 200
        nb_json = json.loads(dl_resp.content.decode("utf-8"))
        assert nb_json["nbformat"] == 4
        assert len(nb_json["cells"]) >= 20

    async def test_package_and_download_artifacts(self, client):
        session_id = await self._setup_session_with_data(client)

        # Train first
        await client.post(
            f"/api/sessions/{session_id}/ml/train",
            json={"target_column": "is_churn", "task_type": "classification", "cv_folds": 2},
        )

        # 1. Package artifacts
        pkg_resp = await client.post(f"/api/sessions/{session_id}/artifacts/package")
        assert pkg_resp.status_code == 200
        pkg_data = pkg_resp.json()
        assert "bundle_path" in pkg_data
        assert pkg_data["filename"].endswith(".zip")

        # 2. Download ZIP bundle
        zip_resp = await client.get(f"/api/sessions/{session_id}/artifacts/download-bundle")
        assert zip_resp.status_code == 200
        assert "zip" in zip_resp.headers["content-type"]

        # Validate ZIP contents
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            names = [n.replace("\\", "/") for n in z.namelist()]
            assert any("final_model.joblib" in n for n in names)
            assert any("model_metadata.json" in n for n in names)
            assert any("inference.py" in n for n in names)
            assert any("README.md" in n for n in names)

        # 3. Download standalone model pipeline (.joblib)
        model_resp = await client.get(f"/api/sessions/{session_id}/model/download")
        assert model_resp.status_code == 200
        assert len(model_resp.content) > 0

