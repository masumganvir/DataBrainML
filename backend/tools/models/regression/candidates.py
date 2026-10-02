"""
DataWise AI — Models: Regression Candidate Estimators
"""

from typing import Any, Dict
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.neighbors import KNeighborsRegressor


def get_regression_candidates(
    n_samples: int = 1000,
    n_features: int = 20,
    include_boosters: bool = True,
) -> Dict[str, Any]:
    """Returns candidate regression estimators with capability detection."""
    models: Dict[str, Any] = {
        "Ridge": Ridge(random_state=42),
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingRegressor(random_state=42),
        "ExtraTrees": ExtraTreesRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "ElasticNet": ElasticNet(random_state=42),
    }

    if n_samples < 5000:
        models["GradientBoosting"] = GradientBoostingRegressor(random_state=42)
        models["KNeighbors"] = KNeighborsRegressor(n_neighbors=5, n_jobs=-1)

    if include_boosters:
        try:
            from xgboost import XGBRegressor
            models["XGBoost"] = XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
            )
        except ImportError:
            pass

        try:
            from lightgbm import LGBMRegressor
            models["LightGBM"] = LGBMRegressor(
                n_estimators=100,
                random_state=42,
                verbose=-1,
                n_jobs=-1,
            )
        except ImportError:
            pass

        try:
            from catboost import CatBoostRegressor
            models["CatBoost"] = CatBoostRegressor(
                iterations=100,
                random_seed=42,
                verbose=False,
                thread_count=-1,
            )
        except ImportError:
            pass

    return models
