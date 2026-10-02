"""
DataWise AI — Feature Selection: Recursive Feature Elimination (RFE)
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression, Ridge


def select_features_rfe(
    X: pd.DataFrame,
    y: pd.Series,
    n_features_to_select: int = 10,
    task_type: str = "classification",
) -> Dict[str, Any]:
    """Iteratively removes weakest features using linear model coefficients."""
    numeric_X = X.select_dtypes(include=[np.number]).fillna(0)
    n_select = min(n_features_to_select, len(numeric_X.columns))
    if n_select == 0:
        return {"selected_features": list(X.columns)}

    estimator = (
        LogisticRegression(max_iter=200, random_state=42)
        if task_type.lower() == "classification"
        else Ridge(random_state=42)
    )

    rfe = RFE(estimator=estimator, n_features_to_select=n_select, step=1)
    rfe.fit(numeric_X, y)

    selected = list(numeric_X.columns[rfe.support_])
    rankings = {col: int(rank) for col, rank in zip(numeric_X.columns, rfe.ranking_)}

    return {
        "method": "RFE",
        "n_features_to_select": n_select,
        "selected_features": selected,
        "rankings": rankings,
    }
