"""
DataWise AI — STEP 7 Tests: Distributions & Correlation Analysis

Tests:
  - Normality statistical tests (Shapiro-Wilk)
  - Skewness categorization and transformation recommendations (log, log1p, yeo-johnson)
  - Pairwise Pearson & Spearman correlation calculation
  - Multicollinearity detection and feature drop recommendations
  - Real dataset tests: skewed_distributions.csv, correlated_features.csv
  - Distribution and correlation API endpoints
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.correlations import CorrelationAnalyzer, analyze_correlations
from app.tools.distributions import analyze_distributions, check_column_normality

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Distribution Analysis
# ------------------------------------------------------------------ #

class TestDistributionAnalyzer:
    def test_normality_and_skewness_detection(self):
        """Should detect normal distributions and recommend log/yeo-johnson for skewed."""
        np.random.seed(42)
        normal_data = np.random.normal(100, 15, 200)
        skewed_data = np.random.exponential(50, 200)

        df = pd.DataFrame({
            "normal_var": normal_data,
            "skewed_var": skewed_data,
        })

        res = analyze_distributions(df)
        cols = {c["column"]: c for c in res["columns"]}

        # Normal feature
        assert cols["normal_var"]["skewness_category"] == "symmetric"
        assert cols["normal_var"]["normality"]["is_normal"] is True
        assert cols["normal_var"]["transformation_recommendation"]["recommended_transformation"] == "none"

        # Skewed feature
        assert cols["skewed_var"]["skewness_category"] in ("moderate_skew", "high_skew")
        assert cols["skewed_var"]["transformation_recommendation"]["recommended_transformation"] in ("log", "log1p", "yeo-johnson")

    def test_yeo_johnson_for_negative_values(self):
        """Should recommend Yeo-Johnson when negative values are present in skewed data."""
        vals = [-10.0, -5.0, 0.0, 1.0, 2.0, 50.0, 100.0, 500.0]
        df = pd.DataFrame({"skewed_neg": vals})
        res = analyze_distributions(df)
        rec = res["columns"][0]["transformation_recommendation"]
        assert rec["recommended_transformation"] == "yeo-johnson"


# ------------------------------------------------------------------ #
#  Unit Tests — Correlation Analyzer
# ------------------------------------------------------------------ #

class TestCorrelationAnalyzer:
    def test_correlation_matrix_and_multicollinearity(self):
        """Should identify collinear pairs (r > 0.85) and recommend resolution."""
        np.random.seed(42)
        base = np.random.normal(0, 1, 100)
        df = pd.DataFrame({
            "feat_a": base,
            "feat_b": base * 1.05 + np.random.normal(0, 0.02, 100),  # collinear r ≈ 0.99
            "feat_c": np.random.normal(0, 1, 100),                   # independent
        })

        res = analyze_correlations(df, threshold=0.80)
        assert res["multicollinearity_risk"] == "HIGH"
        assert res["high_correlation_count"] >= 1

        pair = res["high_correlation_pairs"][0]
        assert set([pair["feature_1"], pair["feature_2"]]) == {"feat_a", "feat_b"}
        assert pair["absolute_r"] >= 0.95
        assert pair["strength"] == "redundant_collinear"
        assert "recommended_keep" in pair["recommendation"]


# ------------------------------------------------------------------ #
#  Integration with Generated Test Datasets
# ------------------------------------------------------------------ #

class TestStep7OnRealData:
    def test_skewed_dataset(self):
        csv_path = DATA_DIR / "skewed_distributions.csv"
        if not csv_path.exists():
            pytest.skip("Test dataset not found.")

        df = pd.read_csv(csv_path)
        res = analyze_distributions(df)
        cols = {c["column"]: c for c in res["columns"]}

        assert "income" in cols
        assert cols["income"]["skewness"] > 0.8

    def test_correlated_dataset(self):
        csv_path = DATA_DIR / "correlated_features.csv"
        if not csv_path.exists():
            pytest.skip("Test dataset not found.")

        df = pd.read_csv(csv_path)
        res = analyze_correlations(df, threshold=0.85)
        assert res["multicollinearity_risk"] == "HIGH"
        assert res["high_correlation_count"] >= 2


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestDistCorrelationsEndpoints:
    async def test_distributions_and_correlations_api(self, client):
        """Tests POST endpoints for distributions and correlations."""
        sess_resp = await client.post("/api/sessions", json={"name": "Dist & Corr Test"})
        session_id = sess_resp.json()["id"]

        csv_content = b"x1,x2,x3\n1,2,10\n2,4,20\n3,6,30\n4,8,40\n5,10,50\n"
        files = {"file": ("dist_corr.csv", io.BytesIO(csv_content), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        # 1. Distributions endpoint
        dist_resp = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/distributions")
        assert dist_resp.status_code == 200
        ddata = dist_resp.json()
        assert ddata["analyzed_columns_count"] == 3

        # 2. Correlations endpoint
        corr_resp = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/correlations")
        assert corr_resp.status_code == 200
        cdata = corr_resp.json()
        assert cdata["columns_count"] == 3
        assert cdata["multicollinearity_risk"] == "HIGH"
        assert len(cdata["high_correlation_pairs"]) >= 1

        # Check session stage transitioned
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "PREPROCESSING_RECOMMENDATIONS"
