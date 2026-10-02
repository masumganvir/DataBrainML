"""
DataWise AI — STEP 8 Tests: Preprocessing Recommendation Engine

Tests:
  - Categorical encoding strategies (binary, one-hot, target, top-k)
  - Feature scaling strategies (StandardScaler, RobustScaler, MinMaxScaler)
  - Power / log transformations
  - Unified Preprocessing recommendation API
  - Destructive action flagging & human approval requirement trigger
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.encoding import recommend_categorical_encoding
from app.tools.scaling import recommend_numerical_scaling
from app.tools.transformation import recommend_transformations

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Encoders, Scalers, Transformers
# ------------------------------------------------------------------ #

class TestPreprocessingRecommendations:
    def test_categorical_encoding_rules(self):
        """Recommends appropriate encoders based on cardinality."""
        n = 100
        df = pd.DataFrame({
            "binary_col": ["yes", "no"] * 50,
            "low_card": ["cat", "dog", "bird"] * 33 + ["cat"],
            "high_card": [f"city_{i}" for i in range(15)] * 6 + ["city_0"] * 10,
            "id_col": [f"ID_{i:04d}" for i in range(n)],
        })

        recs = {r["column"]: r for r in recommend_categorical_encoding(df)}

        assert recs["binary_col"]["strategy"] == "binary_mapping"
        assert recs["low_card"]["encoder_class"] == "OneHotEncoder"
        assert recs["high_card"]["strategy"] in ("target_or_frequency", "frequency_or_top_k")
        assert recs["id_col"]["strategy"] == "drop_or_id"

    def test_numerical_scaling_rules(self):
        """Selects RobustScaler for outliers, MinMaxScaler for bounded, StandardScaler for normal."""
        np.random.seed(42)
        normal_vals = list(np.random.normal(50, 10, 100))
        outlier_vals = list(np.random.normal(50, 10, 100))
        outlier_vals[0] = 500.0
        outlier_vals[1] = 600.0
        outlier_vals[2] = -300.0
        bounded_vals = list(np.random.uniform(0, 1, 100))

        df = pd.DataFrame({
            "normal_feat": normal_vals,
            "outlier_feat": outlier_vals,
            "bounded_feat": bounded_vals,
        })

        recs = {r["column"]: r for r in recommend_numerical_scaling(df)}

        assert recs["outlier_feat"]["scaler_class"] == "RobustScaler"
        assert recs["bounded_feat"]["scaler_class"] == "MinMaxScaler"
        assert recs["normal_feat"]["scaler_class"] == "StandardScaler"

    def test_transformations(self):
        """Recommends log1p for right-skewed with zeros."""
        np.random.seed(42)
        skewed = np.random.exponential(10, 100)
        skewed[0] = 0.0

        df = pd.DataFrame({"exp_feat": skewed})
        recs = recommend_transformations(df)
        assert recs[0]["transformation"] == "log1p"


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestPreprocessingEndpoint:
    async def test_preprocessing_suite_requires_approval_on_destructive(self, client):
        """API should flag destructive operations and trigger HUMAN_APPROVAL stage."""
        sess_resp = await client.post("/api/sessions", json={"name": "Prep Test"})
        session_id = sess_resp.json()["id"]

        # CSV with a column having >50% missing values
        csv_content = b"user_id,age,sparse_notes\nU1,25,hello\nU2,30,\nU3,35,\nU4,40,\n"
        files = {"file": ("sparse.csv", io.BytesIO(csv_content), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        # Request recommendations
        rec_resp = await client.post(
            f"/api/sessions/{session_id}/datasets/{dataset_id}/preprocessing/recommendations"
        )
        assert rec_resp.status_code == 200
        data = rec_resp.json()

        assert "imputation_plan" in data
        assert "encoding_plan" in data
        assert "scaling_plan" in data
        assert "destructive_actions" in data
        assert data["human_approval_required"] is True

        # Check session stage transitioned to HUMAN_APPROVAL
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "HUMAN_APPROVAL"
