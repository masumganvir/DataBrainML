"""
DataWise AI — STEP 6 Tests: Visualization Engine & Endpoints

Tests:
  - Numerical distribution plot with marginal box plot
  - Categorical distribution bar chart
  - Correlation matrix heatmap
  - Missing values summary plot
  - Bivariate scatter plot with trendline
  - Full suite autonomous recommendation
  - API endpoint: suite generation, column-specific plotting, artifact creation
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.tools.visualization import VisualizationEngine

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "test_datasets"


# ------------------------------------------------------------------ #
#  Unit Tests — Visualization Engine
# ------------------------------------------------------------------ #

class TestVisualizationEngine:
    def test_numerical_and_categorical_plots(self, tmp_path):
        """Engine should generate histogram and bar charts with valid specs."""
        df = pd.DataFrame({
            "income": [20000, 35000, 45000, 70000, 95000, 120000],
            "department": ["Sales", "Engineering", "Sales", "HR", "Engineering", "Sales"],
        })
        engine = VisualizationEngine(df, session_id="test_sess_viz")

        # Numerical
        num_res = engine.plot_numerical_distribution("income")
        assert num_res["chart_type"] == "histogram"
        assert "income" in num_res["title"]
        assert Path(num_res["html_path"]).exists()
        assert "figure_json" in num_res
        assert "income" in num_res["interpretation"]

        # Categorical
        cat_res = engine.plot_categorical_distribution("department")
        assert cat_res["chart_type"] == "bar"
        assert Path(cat_res["html_path"]).exists()
        assert "Sales" in cat_res["interpretation"]

    def test_correlation_and_bivariate(self, tmp_path):
        """Engine should generate correlation heatmap and scatter plots."""
        df = pd.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],
            "z": [5.0, 3.0, 2.0, 1.0, 0.5],
        })
        engine = VisualizationEngine(df, session_id="test_sess_biv")

        # Correlation
        corr_res = engine.plot_correlation_heatmap()
        assert corr_res is not None
        assert corr_res["chart_type"] == "heatmap"
        assert Path(corr_res["html_path"]).exists()

        # Bivariate
        biv_res = engine.plot_bivariate("x", "y")
        assert biv_res["chart_type"] == "scatter"
        assert Path(biv_res["html_path"]).exists()
        assert "positive correlation" in biv_res["interpretation"]

    def test_recommended_suite(self):
        """Recommended suite should assemble complete visual portfolio."""
        clean_path = DATA_DIR / "clean_dataset.csv"
        if not clean_path.exists():
            pytest.skip("Test dataset not generated yet.")

        df = pd.read_csv(clean_path).head(100)
        engine = VisualizationEngine(df, session_id="test_sess_suite")
        suite = engine.generate_recommended_suite(max_plots=5)

        assert len(suite) >= 3
        chart_types = [s["chart_type"] for s in suite]
        assert "heatmap" in chart_types
        assert "histogram" in chart_types


# ------------------------------------------------------------------ #
#  API Integration Tests
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
class TestVisualizationEndpoints:
    async def test_visualization_suite_endpoint(self, client):
        """POST suite endpoint generates plots and registers artifacts."""
        sess_resp = await client.post("/api/sessions", json={"name": "Viz Test"})
        session_id = sess_resp.json()["id"]

        csv_content = b"age,salary,dept\n25,50000,Dev\n30,70000,Dev\n35,90000,Mkt\n40,110000,Mkt\n"
        files = {"file": ("viz_data.csv", io.BytesIO(csv_content), "text/csv")}
        up_resp = await client.post(f"/api/sessions/{session_id}/datasets/upload", files=files)
        dataset_id = up_resp.json()["id"]

        suite_resp = await client.post(f"/api/sessions/{session_id}/datasets/{dataset_id}/visualizations/suite")
        assert suite_resp.status_code == 200
        data = suite_resp.json()

        assert len(data["visualizations"]) >= 2

        # Check session stage transitioned
        sess_check = await client.get(f"/api/sessions/{session_id}")
        assert sess_check.json()["current_stage"] == "CORRELATION_ANALYSIS"

        # Check single column endpoint
        col_resp = await client.post(
            f"/api/sessions/{session_id}/datasets/{dataset_id}/visualizations/column/salary"
        )
        assert col_resp.status_code == 200
        assert col_resp.json()["chart_type"] == "histogram"
