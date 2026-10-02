"""
DataWise AI — Models: Time-Series Candidate Estimators
"""

from typing import Any, Dict
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor


def get_time_series_candidates() -> Dict[str, Any]:
    """Returns autoregressive lag-based time-series regressors."""
    return {
        "LaggedRidge": Ridge(random_state=42),
        "LaggedHistGradientBoosting": HistGradientBoostingRegressor(random_state=42),
    }
