"""
DataWise AI — Feature Selection Tools Package
"""

from .variance import filter_low_variance
from .correlation import filter_collinear_features
from .mutual_information import compute_mutual_information
from .select_k_best import select_k_best_features
from .rfe import select_features_rfe
from .permutation import compute_permutation_importance

import pandas as pd
from typing import Any, Dict, List, Optional


FEATURE_SELECTION_MAX_ITERATIONS = 3


def run_feature_selection_suite(
    df: pd.DataFrame,
    target_column: str,
    task_type: str = "classification",
    top_k: int = 15,
) -> Dict[str, Any]:
    """Runs variance filtering, collinearity checks, and feature ranking."""
    X = df.drop(columns=[target_column])
    y = df[target_column]

    var_res = filter_low_variance(X)
    corr_res = filter_collinear_features(X)
    k_best_res = select_k_best_features(X, y, k=top_k, task_type=task_type)

    # Union or intersection recommendation
    recommended = [
        f for f in k_best_res.get("selected_features", [])
        if f not in corr_res.get("dropped_features", [])
        and f not in var_res.get("dropped_features", [])
    ]
    if not recommended:
        recommended = list(X.columns)[:top_k]

    return {
        "variance_filtering": var_res,
        "collinearity_filtering": corr_res,
        "k_best_selection": k_best_res,
        "recommended_features": recommended,
        "original_feature_count": len(X.columns),
        "selected_feature_count": len(recommended),
    }


__all__ = [
    "filter_low_variance",
    "filter_collinear_features",
    "compute_mutual_information",
    "select_k_best_features",
    "select_features_rfe",
    "compute_permutation_importance",
    "run_feature_selection_suite",
    "FEATURE_SELECTION_MAX_ITERATIONS",
]
