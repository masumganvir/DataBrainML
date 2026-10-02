"""
DataWise AI — Models: Classification Candidate Estimators
"""

from typing import Any, Dict, List, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC


def get_classification_candidates(
    n_samples: int = 1000,
    n_features: int = 20,
    include_boosters: bool = True,
) -> Dict[str, Any]:
    """Returns candidate classification estimators with capability detection."""
    models: Dict[str, Any] = {
        "LogisticRegression": LogisticRegression(max_iter=500, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=42),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        "KNeighbors": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
    }

    if n_samples < 5000:
        models["GradientBoosting"] = GradientBoostingClassifier(random_state=42)
        models["GaussianNB"] = GaussianNB()

    if include_boosters:
        # XGBoost capability check
        try:
            from xgboost import XGBClassifier
            models["XGBoost"] = XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                random_state=42,
                eval_metric="logloss",
                n_jobs=-1,
            )
        except ImportError:
            pass

        # LightGBM capability check
        try:
            from lightgbm import LGBMClassifier
            models["LightGBM"] = LGBMClassifier(
                n_estimators=100,
                random_state=42,
                verbose=-1,
                n_jobs=-1,
            )
        except ImportError:
            pass

        # CatBoost capability check
        try:
            from catboost import CatBoostClassifier
            models["CatBoost"] = CatBoostClassifier(
                iterations=100,
                random_seed=42,
                verbose=False,
                thread_count=-1,
            )
        except ImportError:
            pass

    return models
