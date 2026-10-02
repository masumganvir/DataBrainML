"""
DataWise AI — Feature Tools
Deterministic feature engineering, interactions, selection, and pipeline building.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from app.tools.feature_engineering import FeatureEngineer
from app.tools.feature_selection import FeatureSelector
from app.tools.pipeline_builder import build_column_transformer, build_pipeline as build_sklearn_pipeline


def engineer_features(df: pd.DataFrame, target_col: Optional[str] = None, max_new_features: int = 20) -> Dict[str, Any]:
    fe = FeatureEngineer(df, target_column=target_col)
    recs = fe.generate_all_recommendations()
    return {
        "recommendations": recs[:max_new_features],
        "engineered_feature_names": [r["new_columns"][0] for r in recs[:max_new_features] if "new_columns" in r and r["new_columns"]],
        "total_recommended": len(recs)
    }


def generate_interaction_features(df: pd.DataFrame, max_interactions: int = 5) -> pd.DataFrame:
    fe = FeatureEngineer(df)
    recs = fe.generate_ratio_features()[:max_interactions]
    if not recs:
        recs = fe._polynomial_features()[:max_interactions]
    return fe.apply_plan(df, recs) if recs else df.copy()



def generate_datetime_features(df: pd.DataFrame) -> pd.DataFrame:
    fe = FeatureEngineer(df)
    recs = fe.generate_datetime_features()
    return fe.apply_plan(df, recs)


def select_features(df: pd.DataFrame, target_col: Optional[str] = None, k: int = 15) -> Dict[str, Any]:
    fs = FeatureSelector(df, target_column=target_col)
    res = fs.run_all()
    return {
        "selected_features": res.get("selected_features", list(df.columns[:k])),
        "dropped_features": res.get("dropped_features", []),
        "scores": res.get("scores", {}),
        "strategies_applied": ["variance_threshold", "correlation_filter", "mutual_info"]
    }


__all__ = [
    "FeatureEngineer",
    "FeatureSelector",
    "engineer_features",
    "generate_interaction_features",
    "generate_datetime_features",
    "select_features",
    "build_column_transformer",
    "build_sklearn_pipeline",
]
