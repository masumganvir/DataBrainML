"""
DataWise AI — Tests for Steps 14-16:
Pipeline Builder & ML Recommendation Engine
"""

import pandas as pd
import pytest

from app.tools.ml_recommender import MLRecommender, compute_ml_readiness
from app.tools.pipeline_builder import PipelineBuilder


@pytest.fixture
def sample_pipeline_df():
    return pd.DataFrame({
        "age": [25, 30, 35, 40, 45],
        "income": [50000.0, 60000.0, 75000.0, 90000.0, 110000.0],
        "city": ["New York", "Paris", "London", "Paris", "London"],
        "purchased": [0, 1, 0, 1, 1],
    })


def test_pipeline_builder(sample_pipeline_df):
    builder = PipelineBuilder(
        df=sample_pipeline_df,
        target_column="purchased",
        task_type="classification",
        selected_features=["age", "income", "city"],
    )
    result = builder.build()
    
    assert "generated_code" in result
    assert "numerical_columns" in result
    code = result["generated_code"]
    assert "ColumnTransformer" in code
    assert "Pipeline" in code
    assert "StandardScaler" in code or "OneHotEncoder" in code


def test_ml_recommender():
    recommender = MLRecommender(
        task_type="classification",
        row_count=5000,
        col_count=20,
        is_imbalanced=True,
    )
    res = recommender.recommend()
    
    assert "task_type" in res
    assert res["task_type"] == "classification"
    assert "ml_readiness" in res
    assert "recommendations" in res
    assert len(res["recommendations"]) > 0
    assert "roadmap" in res


def test_compute_ml_readiness():
    readiness = compute_ml_readiness(
        row_count=1000,
        col_count=10,
        missing_pct_avg=0.02,
        high_severity_missing=0,
        duplicate_pct=0.0,
        outlier_severity="mild",
        leakage_warnings=0,
        has_target=True,
    )
    assert readiness["score"] >= 70
    assert readiness["level"] in ("READY_FOR_BASELINE", "NEEDS_PREPROCESSING")
