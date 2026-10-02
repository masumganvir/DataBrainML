"""
DataWise AI — STEP 3 Tests: Dataset Profiler Tool & Endpoints

Tests:
  - Numerical statistics calculation (mean, std, median, IQR, skewness)
  - Column type classification (numerical, categorical, binary, datetime, text)
  - Anomaly detection (constants, near-constants, identifier columns)
  - Profiling real test datasets (clean_dataset.csv, mixed_types.csv)
  - Analysis API endpoint (POST & GET profile)
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.profiler import DatasetProfiler, profile_dataframe

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Profiler Engine
# ------------------------------------------------------------------ #

class TestProfilerEngine:
    def test_numerical_statistics(self):
        """Profiler should accurately calculate mean, median, IQR, std, skewness."""
        np.random.seed(42)
        data = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 100.0])
        df = pd.DataFrame({"metric": data})

        result = profile_dataframe(df)
        assert result["total_rows"] == 6
        assert result["total_columns"] == 1

        prof = result["column_profiles"][0]
        assert prof["name"] == "metric"
        assert prof["mean"] == pytest.approx(41.6667, rel=1e-3)
        assert prof["median"] == pytest.approx(35.0, rel=1e-3)
        assert prof["min"] == 10.0
        assert prof["max"] == 100.0
        assert prof["q1"] == pytest.approx(22.5, rel=1e-2)
        assert prof["q3"] == pytest.approx(47.5, rel=1e-2)
        assert prof["iqr"] > 0
        assert prof["skewness"] > 0  # right skewed

    def test_column_type_classification(self):
        """Profiler should properly classify binary, datetime, text, categorical, numerical."""
        df = pd.DataFrame({
            "num_col": [1.5, 2.5, 3.5, 4.5, 5.5],
            "bin_col": [0, 1, 0, 1, 0],
            "cat_col": ["red", "blue", "green", "red", "blue"],
            "date_col": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "text_col": [
                "This is a relatively long customer review description",
                "Another detailed customer feedback sentence for analysis",
                "Yet another rich textual feedback review comment",
                "Fourth sample text row for NLP feature testing",
                "Fifth paragraph of text describing customer experience",
            ],
        })

        result = profile_dataframe(df)
        cls = result["classification"]

        assert "num_col" in cls["numerical"]
        assert "bin_col" in cls["binary"]
        assert "cat_col" in cls["categorical"]
        assert "date_col" in cls["datetime"]
        assert "text_col" in cls["text"]

    def test_suspicious_columns_detection(self):
        """Profiler should identify constants, near-constants, and identifiers."""
        n = 100
        df = pd.DataFrame({
            "user_id": [f"USR_{i:04d}" for i in range(n)],           # ID
            "constant_val": ["fixed"] * n,                              # Constant
            "near_constant": ["common"] * 96 + ["rare"] * 4,            # 96% -> Near constant
            "normal_cat": ["A", "B", "C", "D"] * 25,
        })

        result = profile_dataframe(df)
        cls = result["classification"]

        assert "user_id" in cls["identifiers"]
        assert "constant_val" in cls["constants"]
        assert "near_constant" in cls["near_constants"]
        assert "normal_cat" not in cls["constants"]
        assert "normal_cat" not in cls["near_constants"]


# ------------------------------------------------------------------ #
#  Integration with Generated Test Datasets
# ------------------------------------------------------------------ #

class TestProfilerOnRealData:
    def test_profile_clean_dataset(self):
        clean_path = DATA_DIR / "clean_dataset.csv"
        if not clean_path.exists():
            pytest.skip("Test dataset not generated yet.")

        df = pd.read_csv(clean_path)
        result = profile_dataframe(df)

        assert result["total_rows"] == 1000
        assert result["total_columns"] == 12
        assert "customer_id" in result["classification"]["identifiers"]
        assert "churn" in result["classification"]["binary"]
        assert "monthly_charges" in result["classification"]["numerical"]

    def test_profile_mixed_types_dataset(self):
        mixed_path = DATA_DIR / "mixed_types.csv"
        if not mixed_path.exists():
            pytest.skip("Test dataset not generated yet.")

        df = pd.read_csv(mixed_path)
        result = profile_dataframe(df)

        cls = result["classification"]
        assert "user_id" in cls["identifiers"]
        assert "data_source" in cls["constants"]
        assert "verified" in cls["near_constants"]


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestAnalysisEndpoints:
    async def test_post_and_get_dataset_profile(self, client):
        """Testing profile generation and retrieval via API."""
        # 1. Create Session
        sess_resp = await client.post("/api/sessions", json={"name": "Profiler Test"})
        session_id = sess_resp.json()["id"]

        # 2. Upload CSV
        csv_bytes = b"age,income,is_fraud\n25,50000,0\n35,75000,0\n45,120000,1\n"
        files = {"file": ("profile_test.csv", io.BytesIO(csv_bytes), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        # 3. Post profile
        prof_post = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/profile")
        assert prof_post.status_code == 200
        pdata = prof_post.json()

        assert pdata["total_rows"] == 3
        assert pdata["total_columns"] == 3
        assert "age" in pdata["classification"]["numerical"]
        assert "is_fraud" in pdata["classification"]["binary"]

        # Check session stage transitioned to DATA_QUALITY
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "DATA_QUALITY"

        # 4. Get cached profile
        prof_get = await client.get(f"/api/sessions/{session_id}/datasets/{dataset_id}/profile")
        assert prof_get.status_code == 200
        assert prof_get.json()["total_rows"] == 3
