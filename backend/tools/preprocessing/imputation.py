"""
DataWise AI — Preprocessing: Imputation Strategy Builder
"""

from typing import Any, Dict, List, Optional
from sklearn.impute import KNNImputer, SimpleImputer


def create_numeric_imputer(strategy: str = "median", fill_value: Optional[float] = None) -> Any:
    """Instantiates a scikit-learn imputer for numerical features."""
    strat = strategy.lower()
    if strat in ("mean", "median", "most_frequent"):
        return SimpleImputer(strategy=strat)
    elif strat == "constant":
        return SimpleImputer(strategy="constant", fill_value=fill_value if fill_value is not None else 0.0)
    elif strat == "knn":
        return KNNImputer(n_neighbors=5)
    elif strat == "iterative":
        try:
            from sklearn.experimental import enable_iterative_imputer  # noqa: F401
            from sklearn.impute import IterativeImputer
            return IterativeImputer(random_state=42, max_iter=10)
        except Exception:
            return SimpleImputer(strategy="median")
    return SimpleImputer(strategy="median")


def create_categorical_imputer(strategy: str = "most_frequent", fill_value: str = "Unknown") -> Any:
    """Instantiates a scikit-learn imputer for categorical features."""
    strat = strategy.lower()
    if strat == "constant" or strat == "unknown":
        return SimpleImputer(strategy="constant", fill_value=fill_value)
    return SimpleImputer(strategy="most_frequent")
