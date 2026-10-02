"""
DataWise AI — Evaluation: Regression Metrics
"""

from typing import Any, Dict
import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


def evaluate_regression(
    y_true: Any,
    y_pred: Any,
) -> Dict[str, Any]:
    """Calculates MAE, MSE, RMSE, R2, and residual statistics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))

    residuals = np.array(y_true) - np.array(y_pred)
    res_mean = float(np.mean(residuals))
    res_std = float(np.std(residuals))

    return {
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "residual_mean": round(res_mean, 4),
        "residual_std": round(res_std, 4),
    }
