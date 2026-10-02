"""
DataWise AI — Evaluation: Learning Curves
"""

from typing import Any, Dict, List
import numpy as np
from sklearn.model_selection import learning_curve


def generate_learning_curve_data(
    estimator: Any,
    X: Any,
    y: Any,
    cv: int = 5,
    train_sizes: List[float] = None,
) -> Dict[str, Any]:
    """Computes train and validation performance curves across sample sizes."""
    if train_sizes is None:
        train_sizes = [0.2, 0.4, 0.6, 0.8, 1.0]

    sizes, train_scores, val_scores = learning_curve(
        estimator,
        X,
        y,
        cv=cv,
        train_sizes=train_sizes,
        n_jobs=-1,
        random_state=42,
    )

    return {
        "train_sizes": [int(s) for s in sizes],
        "train_scores_mean": [round(float(s), 4) for s in np.mean(train_scores, axis=1)],
        "train_scores_std": [round(float(s), 4) for s in np.std(train_scores, axis=1)],
        "val_scores_mean": [round(float(s), 4) for s in np.mean(val_scores, axis=1)],
        "val_scores_std": [round(float(s), 4) for s in np.std(val_scores, axis=1)],
    }
