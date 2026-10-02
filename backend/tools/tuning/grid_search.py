"""
DataWise AI — Tuning: Grid Search Hyperparameter Optimization
"""

from typing import Any, Dict
from sklearn.model_selection import GridSearchCV


def run_grid_search(
    estimator: Any,
    param_grid: Dict[str, list],
    X: Any,
    y: Any,
    cv: int = 3,
    scoring: str = "f1_weighted",
) -> Dict[str, Any]:
    """Exhaustive search over specified parameter values."""
    search = GridSearchCV(
        estimator=estimator,
        param_grid=param_grid,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        refit=True,
    )
    search.fit(X, y)

    return {
        "best_params": search.best_params_,
        "best_score": round(float(search.best_score_), 4),
        "best_estimator": search.best_estimator_,
        "n_splits": cv,
    }
