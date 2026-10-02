"""
DataWise AI — Tuning: Randomized Search Hyperparameter Optimization
"""

from typing import Any, Dict
from sklearn.model_selection import RandomizedSearchCV


def run_random_search(
    estimator: Any,
    param_distributions: Dict[str, Any],
    X: Any,
    y: Any,
    n_iter: int = 20,
    cv: int = 3,
    scoring: str = "f1_weighted",
) -> Dict[str, Any]:
    """Randomized search over hyperparameter distributions within bounded trials."""
    search = RandomizedSearchCV(
        estimator=estimator,
        param_distributions=param_distributions,
        n_iter=n_iter,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        random_state=42,
        refit=True,
    )
    search.fit(X, y)

    return {
        "best_params": search.best_params_,
        "best_score": round(float(search.best_score_), 4),
        "best_estimator": search.best_estimator_,
        "n_iter": n_iter,
    }
