"""
DataWise AI — Feature Selection: Statistical SelectKBest (ANOVA / Chi2 / F-regression)
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif, f_regression


def select_k_best_features(
    X: pd.DataFrame,
    y: pd.Series,
    k: int = 10,
    task_type: str = "classification",
) -> Dict[str, Any]:
    """Selects top K features based on univariate statistical tests."""
    numeric_X = X.select_dtypes(include=[np.number]).fillna(0)
    k_actual = min(k, len(numeric_X.columns))
    if k_actual == 0:
        return {"selected_features": list(X.columns)}

    score_func = f_classif if task_type.lower() == "classification" else f_regression
    selector = SelectKBest(score_func=score_func, k=k_actual)
    selector.fit(numeric_X, y)

    selected = list(numeric_X.columns[selector.get_support()])
    scores = {col: round(float(s), 4) for col, s in zip(numeric_X.columns, selector.scores_)}

    return {
        "method": "SelectKBest",
        "k": k_actual,
        "selected_features": selected,
        "scores": scores,
    }
