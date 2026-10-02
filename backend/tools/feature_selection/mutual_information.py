"""
DataWise AI — Feature Selection: Mutual Information
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def compute_mutual_information(
    X: pd.DataFrame,
    y: pd.Series,
    task_type: str = "classification",
    top_k: int = 20,
) -> Dict[str, Any]:
    """Computes non-linear dependency mutual information scores."""
    numeric_X = X.select_dtypes(include=[np.number]).fillna(0)
    if len(numeric_X.columns) == 0:
        return {"scores": {}}

    if task_type.lower() == "classification":
        mi = mutual_info_classif(numeric_X, y, random_state=42)
    else:
        mi = mutual_info_regression(numeric_X, y, random_state=42)

    scores = {col: round(float(score), 4) for col, score in zip(numeric_X.columns, mi)}
    sorted_features = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "method": "Mutual Information",
        "task_type": task_type,
        "ranking": [{"feature": k, "score": v} for k, v in sorted_features[:top_k]],
        "top_features": [k for k, _ in sorted_features[:top_k]],
    }
