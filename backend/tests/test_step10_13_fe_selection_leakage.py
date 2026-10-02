"""
DataWise AI — Tests for Steps 10-13:
Feature Engineering, Selection, Target Detection & Leakage
"""

import numpy as np
import pandas as pd
import pytest

from app.tools.feature_engineering import FeatureEngineer
from app.tools.feature_selection import FeatureSelector
from app.tools.target_detector import TargetDetector
from app.tools.leakage import LeakageDetector


@pytest.fixture
def sample_fe_df():
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "timestamp": dates,
        "price": np.random.exponential(10, size=n) + 1.0,
        "quantity": np.random.randint(1, 20, size=n),
        "category": np.random.choice(["Electronics", "Clothing", "Food"], size=n),
        "target": np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
    })
    # Add a leaky column that directly exposes target
    df["leaky_target_indicator"] = df["target"] * 1.0 + np.random.normal(0, 0.0001, size=n)
    return df


def test_feature_engineering_recommendations(sample_fe_df):
    fe = FeatureEngineer(df=sample_fe_df, target_column="target", task_type="classification")
    recs = fe.recommend_features()
    assert "operations" in recs
    assert "new_feature_names" in recs
    assert recs["total_new_features"] >= 1
    
    # Test applying plan
    transformed_df = fe.apply_plan(sample_fe_df, recs["operations"])
    assert len(transformed_df.columns) > len(sample_fe_df.columns)


def test_target_detection(sample_fe_df):
    detector = TargetDetector(sample_fe_df)
    report = detector.detect()
    assert "candidates" in report
    candidate_cols = [c["column"] for c in report["candidates"]]
    assert "target" in candidate_cols
    assert report["recommended_task"] in ("classification", "regression")


def test_leakage_detection(sample_fe_df):
    detector = LeakageDetector(df=sample_fe_df, target_column="target", task_type="classification")
    report = detector.detect()
    warnings = report.get("warnings", [])
    leaky_cols = [w["column"] for w in warnings]
    assert "leaky_target_indicator" in leaky_cols


def test_feature_selection(sample_fe_df):
    selector = FeatureSelector(df=sample_fe_df, target_column="target", task_type="classification")
    report = selector.run_all()
    assert "selected_features" in report
    assert len(report["selected_features"]) > 0
