"""
DataWise AI — STEP 5 Tests: Outlier Analyzer Tool & Endpoints

Tests:
  - IQR, Z-Score, and MAD outlier detection on known distributions
  - Isolation Forest multivariate detection
  - Outlier severity levels (none, mild, moderate, severe)
  - Detection on outliers_dataset.csv
  - Outlier API endpoints (POST & GET)
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.outliers import (
    OutlierAnalyzer,
    analyze_dataset_outliers,
    classify_outlier_severity,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Outlier Analyzer
# ------------------------------------------------------------------ #

class TestOutlierAnalyzer:
    def test_severity_classification(self):
        """Maps outlier percentages correctly."""
        assert classify_outlier_severity(0.0) == "none"
        assert classify_outlier_severity(1.2) == "mild"
        assert classify_outlier_severity(3.5) == "moderate"
        assert classify_outlier_severity(8.0) == "severe"

    def test_iqr_and_zscore_detection(self):
        """Should detect known injected extreme values."""
        np.random.seed(42)
        base = np.random.normal(50, 5, 100).tolist()
        # Inject extreme outliers
        base.append(500.0)
        base.append(-200.0)

        df = pd.DataFrame({"salary": base})
        analyzer = OutlierAnalyzer(df)

        iqr_reports = analyzer.analyze_iqr(multiplier=1.5)
        assert len(iqr_reports) == 1
        assert iqr_reports[0]["outlier_count"] >= 2
        assert iqr_reports[0]["severity"] in ("mild", "moderate")

        z_reports = analyzer.analyze_zscore(threshold=3.0)
        assert len(z_reports) == 1
        assert z_reports[0]["outlier_count"] >= 2

    def test_mad_detection(self):
        """MAD should detect outliers robustly."""
        vals = [10, 10, 11, 10, 12, 10, 9, 10, 11, 10, 100]
        df = pd.DataFrame({"measurement": vals})
        analyzer = OutlierAnalyzer(df)

        mad_reports = analyzer.analyze_mad(threshold=3.5)
        assert len(mad_reports) == 1
        assert mad_reports[0]["outlier_count"] >= 1
        assert mad_reports[0]["upper_bound"] < 100

    def test_isolation_forest(self):
        """Isolation Forest should return anomaly indices and stats."""
        n = 100
        df = pd.DataFrame({
            "feat_1": np.random.normal(0, 1, n),
            "feat_2": np.random.normal(0, 1, n),
        })
        # Inject an anomaly far outside the cluster
        df.loc[0, "feat_1"] = 15.0
        df.loc[0, "feat_2"] = 15.0

        analyzer = OutlierAnalyzer(df)
        iso = analyzer.analyze_isolation_forest(contamination=0.03)

        assert iso["method"] == "Isolation Forest"
        assert iso["outlier_count"] > 0
        assert 0 in iso["sample_outlier_indices"]


# ------------------------------------------------------------------ #
#  Integration with Generated Test Datasets
# ------------------------------------------------------------------ #

class TestOutliersOnRealData:
    def test_outliers_dataset(self):
        csv_path = DATA_DIR / "outliers_dataset.csv"
        if not csv_path.exists():
            pytest.skip("Test dataset not found.")

        df = pd.read_csv(csv_path)
        res = analyze_dataset_outliers(df)

        iqr_by_col = {r["column"]: r for r in res["iqr_reports"]}
        assert "monthly_charges" in iqr_by_col
        assert iqr_by_col["monthly_charges"]["outlier_count"] >= 15
        assert iqr_by_col["monthly_charges"]["severity"] in ("moderate", "severe")


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestOutlierEndpoints:
    async def test_outlier_endpoints(self, client):
        """Verify POST and GET for outlier analysis."""
        sess_resp = await client.post("/api/sessions", json={"name": "Outliers Test"})
        session_id = sess_resp.json()["id"]

        csv_content = b"val\n10\n11\n10\n12\n9\n10\n500\n"
        files = {"file": ("outlier_test.csv", io.BytesIO(csv_content), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        post_resp = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/outliers")
        assert post_resp.status_code == 200
        odata = post_resp.json()

        assert "val" in odata["numerical_columns_analyzed"]
        assert len(odata["iqr_reports"]) == 1
        assert odata["iqr_reports"][0]["outlier_count"] == 1

        # Check session stage transitioned to VISUALIZATION
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "VISUALIZATION"

        # Check GET endpoint
        get_resp = await client.get(f"/api/sessions/{session_id}/datasets/{dataset_id}/outliers")
        assert get_resp.status_code == 200
        assert len(get_resp.json()["iqr_reports"]) == 1
