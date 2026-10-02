"""
DataWise AI — Feature Selection: Permutation Importance
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


def compute_permutation_importance(
    X: pd.DataFrame,
    y: pd.Series,
    task_type: str = "classification",
    top_k: int = 15,
) -> Dict[str, Any]:
    """Measures model score degradation when feature values are randomly shuffled."""
    numeric_X = X.select_dtypes(include=[np.number]).fillna(0)
    if len(numeric_X.columns) == 0:
        return {"scores": {}}

    model = (
        RandomForestClassifier(n_estimators=40, random_state=42, max_depth=6)
        if task_type.lower() == "classification"
        else RandomForestRegressor(n_estimators=40, random_state=42, max_depth=6)
    )
    model.fit(numeric_X, y)

    res = permutation_importance(model, numeric_X, y, n_repeats=5, random_state=42, n_jobs=-1)

    importances = {
        col: round(float(mean), 4)
        for col, mean in zip(numeric_X.columns, res.importances_mean)
    }
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)

    return {
        "method": "Permutation Importance",
        "ranking": [{"feature": k, "importance": v} for k, v in sorted_importances[:top_k]],
        "top_features": [k for k, _ in sorted_importances[:top_k]],
    }
