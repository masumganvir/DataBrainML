"""
DataWise AI — Tests for Step 20: Reports & Roadmaps
"""

import pytest
from app.reports.report_generator import (
    generate_markdown_report,
    generate_html_report,
    generate_ml_roadmap,
)
from app.state.data_science_state import DataScienceState


@pytest.fixture
def mock_state() -> DataScienceState:
    return {
        "session_id": "test-session-xyz",
        "dataset_id": "test-ds-123",
        "dataset_metadata": {
            "filename": "test_churn.csv",
            "row_count": 2500,
            "col_count": 12,
            "size_bytes": 102400,
        },
        "target_column": "churn",
        "task_type": "classification",
        "numerical_columns": ["tenure", "monthly_charges", "total_charges"],
        "categorical_columns": ["contract", "payment_method", "internet_service"],
        "missing_value_report": [
            {
                "column": "total_charges",
                "missing_count": 11,
                "missing_pct": 0.44,
                "severity": "LOW",
                "recommended_strategy": "median",
            }
        ],
        "outlier_report": [
            {
                "column": "monthly_charges",
                "method": "IQR",
                "outlier_count": 5,
                "outlier_pct": 0.2,
                "severity": "mild",
            }
        ],
        "duplicate_report": {"duplicate_count": 0, "duplicate_pct": 0.0},
        "ml_readiness_score": 85.5,
        "ml_readiness_level": "READY_FOR_BASELINE",
        "selected_features": ["tenure", "monthly_charges", "contract"],
        "engineered_features": ["tenure_squared"],
        "model_recommendations": [
            {
                "model_name": "Gradient Boosting",
                "model_class": "xgboost.XGBClassifier",
                "rationale": "High tabular performance",
                "pros": ["Handles missing values"],
                "cons": ["Requires tuning"],
                "evaluation_metrics": ["roc_auc", "f1_weighted"],
            }
        ],
        "leakage_warnings": [],
    }


def test_markdown_report_generation(mock_state):
    md = generate_markdown_report(mock_state)
    assert "# DataWise AI — Data Intelligence" in md

    assert "test_churn.csv" in md
    assert "85.5/100" in md
    assert "total_charges" in md
    assert "Gradient Boosting" in md


def test_html_report_generation(mock_state):
    html = generate_html_report(mock_state)
    assert "<!DOCTYPE html>" in html
    assert "test_churn.csv" in html
    assert "85.5" in html
    assert "Gradient Boosting" in html
    assert "total_charges" in html
    assert "@media print" in html  # Ensures print-friendly CSS exists


def test_ml_roadmap_generation(mock_state):
    roadmap = generate_ml_roadmap(mock_state)
    assert "# Machine Learning Engineering Roadmap: `test_churn.csv`" in roadmap
    assert "Phase 1: Problem Formulation" in roadmap
    assert "Phase 2: Data Pipeline" in roadmap
    assert "Phase 7: Production Serving & Deployment" in roadmap
    assert "Phase 8: MLOps, Monitoring & Continuous Retraining" in roadmap
