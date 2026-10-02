"""
DataWise AI — Models Tools Package
"""

from .classification import get_classification_candidates
from .regression import get_regression_candidates
from .clustering import get_clustering_candidates
from .time_series import get_time_series_candidates

from typing import Any, Dict


def get_candidate_models(
    task_type: str = "classification",
    n_samples: int = 1000,
    n_features: int = 20,
) -> Dict[str, Any]:
    """Factory retrieving candidate models tailored to task and scale."""
    t = task_type.lower()
    if t == "classification":
        return get_classification_candidates(n_samples=n_samples, n_features=n_features)
    elif t == "regression":
        return get_regression_candidates(n_samples=n_samples, n_features=n_features)
    elif t == "clustering":
        return get_clustering_candidates()
    elif t in ("time_series", "forecasting"):
        return get_time_series_candidates()
    return get_classification_candidates(n_samples=n_samples, n_features=n_features)


__all__ = [
    "get_classification_candidates",
    "get_regression_candidates",
    "get_clustering_candidates",
    "get_time_series_candidates",
    "get_candidate_models",
]
