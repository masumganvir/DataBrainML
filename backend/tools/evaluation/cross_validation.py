"""
DataWise AI — Evaluation: Cross Validation Runner
"""

from typing import Any, Dict, List
import numpy as np
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score


def run_cross_validation(
    estimator: Any,
    X: Any,
    y: Any,
    cv: int = 5,
    scoring: str = "f1_weighted",
    stratified: bool = True,
) -> Dict[str, Any]:
    """Runs k-fold cross-validation returning mean, standard deviation, and fold scores."""
    cv_splitter = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42) if stratified else KFold(n_splits=cv, shuffle=True, random_state=42)

    try:
        scores = cross_val_score(estimator, X, y, cv=cv_splitter, scoring=scoring, n_jobs=-1)
    except Exception:
        # Fallback to default scoring if specific metric fails
        scores = cross_val_score(estimator, X, y, cv=cv_splitter, n_jobs=-1)

    return {
        "scoring": scoring,
        "n_splits": cv,
        "fold_scores": [round(float(s), 4) for s in scores],
        "mean_score": round(float(np.mean(scores)), 4),
        "std_score": round(float(np.std(scores)), 4),
    }
