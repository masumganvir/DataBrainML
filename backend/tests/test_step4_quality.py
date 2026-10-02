"""
DataWise AI — STEP 4 Tests: Quality & Missing Value Analyzer

Tests:
  - Missing value severity levels (NONE, LOW, MEDIUM, HIGH, CRITICAL)
  - Imputation strategy recommendations (mean, median for skewed, mode for categorical, drop for critical)
  - Duplicate rows identification and sample collection
  - Real dataset tests: missing_values_dataset.csv, duplicate_rows.csv
  - Quality API endpoint (POST & GET quality)
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.quality import QualityAnalyzer, analyze_data_quality, classify_missing_severity

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Quality Analyzer
# ------------------------------------------------------------------ #

class TestQualityAnalyzer:
    def test_missing_severity_classification(self):
        """Severity helper should strictly follow defined thresholds."""
        assert classify_missing_severity(0.0) == "NONE"
        assert classify_missing_severity(3.5) == "LOW"
        assert classify_missing_severity(12.0) == "MEDIUM"
        assert classify_missing_severity(35.0) == "HIGH"
        assert classify_missing_severity(55.0) == "CRITICAL"

    def test_imputation_recommendations(self):
        """Should recommend median for skewed, mean for normal, and drop for critical."""
        n = 100
        # Normal distribution
        normal_vals = list(np.random.normal(50, 10, n))
        normal_vals[0] = np.nan
        normal_vals[1] = np.nan

        # Skewed distribution (exponential)
        skewed_vals = list(np.random.exponential(50, n))
        skewed_vals[0] = np.nan
        skewed_vals[1] = np.nan

        # Critical missing (>50%)
        crit_vals = [1.0] * 30 + [np.nan] * 70

        # Categorical
        cat_vals = ["A", "B", "A", "A"] * 24 + [np.nan] * 4

        df = pd.DataFrame({
            "normal_feat": normal_vals,
            "skewed_feat": skewed_vals,
            "critical_feat": crit_vals,
            "cat_feat": cat_vals,
        })

        res = analyze_data_quality(df)
        reports = {r["column"]: r for r in res["missing_reports"]}

        assert reports["normal_feat"]["recommended_strategy"] in ("mean", "median")
        assert reports["skewed_feat"]["recommended_strategy"] == "median"
        assert reports["critical_feat"]["severity"] == "CRITICAL"
        assert reports["critical_feat"]["recommended_strategy"] == "drop_column"
        assert reports["cat_feat"]["recommended_strategy"] == "most_frequent"

    def test_duplicate_row_detection(self):
        """Analyzer should detect duplicate rows and return sample records."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 1, 2],
            "val": ["a", "b", "c", "a", "b"],
        })
        res = analyze_data_quality(df)
        dups = res["duplicates"]

        assert dups["has_duplicates"] is True
        assert dups["duplicate_count"] == 2
        assert dups["duplicate_pct"] == 40.0
        assert len(dups["sample_duplicates"]) == 2


# ------------------------------------------------------------------ #
#  Integration with Generated Test Datasets
# ------------------------------------------------------------------ #

class TestQualityOnRealData:
    def test_missing_values_dataset(self):
        csv_path = DATA_DIR / "missing_values_dataset.csv"
        if not csv_path.exists():
            pytest.skip("Test dataset not found.")

        df = pd.read_csv(csv_path)
        res = analyze_data_quality(df)

        assert res["columns_with_missing_count"] >= 4
        reports = {r["column"]: r for r in res["missing_reports"]}

        # Age had 3% missing -> LOW
        assert reports["age"]["severity"] == "LOW"
        # Total charges had 55% missing -> CRITICAL
        assert reports["total_charges"]["severity"] == "CRITICAL"
        assert reports["total_charges"]["recommended_strategy"] == "drop_column"

    def test_duplicate_rows_dataset(self):
        csv_path = DATA_DIR / "duplicate_rows.csv"
        if not csv_path.exists():
            pytest.skip("Test dataset not found.")

        df = pd.read_csv(csv_path)
        res = analyze_data_quality(df)

        assert res["duplicates"]["has_duplicates"] is True
        assert res["duplicates"]["duplicate_count"] > 0


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestQualityEndpoints:
    async def test_quality_analysis_endpoint(self, client):
        """Test quality endpoint POST and GET."""
        sess_resp = await client.post("/api/sessions", json={"name": "Quality Test"})
        session_id = sess_resp.json()["id"]

        csv_content = b"a,b,c\n1,2,3\n1,2,3\n4,,6\n"
        files = {"file": ("quality.csv", io.BytesIO(csv_content), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        # Run quality scan
        post_resp = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/quality")
        assert post_resp.status_code == 200
        qdata = post_resp.json()

        assert qdata["total_rows"] == 3
        assert qdata["duplicates"]["has_duplicates"] is True
        assert qdata["duplicates"]["duplicate_count"] == 1
        assert qdata["columns_with_missing_count"] == 1

        # Check session stage transitioned
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "OUTLIER_DETECTION"

        # Get cached
        get_resp = await client.get(f"/api/sessions/{session_id}/datasets/{dataset_id}/quality")
        assert get_resp.status_code == 200
        assert get_resp.json()["total_rows"] == 3
