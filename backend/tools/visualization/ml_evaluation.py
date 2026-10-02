"""
DataWise AI — Visualization: Machine Learning Evaluation Charts
"""

from typing import Any, Dict, List
import numpy as np


def generate_confusion_matrix_spec(
    labels: List[str],
    matrix: List[List[int]],
) -> Dict[str, Any]:
    """Generates structured confusion matrix spec."""
    return {
        "plot_type": "confusion_matrix",
        "labels": labels,
        "matrix": matrix,
    }


def generate_roc_curve_spec(
    fpr: List[float],
    tpr: List[float],
    auc_score: float,
) -> Dict[str, Any]:
    """Generates downsampled ROC curve data points."""
    # Downsample to ~50 points
    if len(fpr) > 60:
        indices = np.linspace(0, len(fpr) - 1, 50, dtype=int)
        fpr = [float(fpr[i]) for i in indices]
        tpr = [float(tpr[i]) for i in indices]

    return {
        "plot_type": "roc_curve",
        "fpr": [round(x, 4) for x in fpr],
        "tpr": [round(y, 4) for y in tpr],
        "auc": round(auc_score, 4),
    }


def generate_residuals_spec(
    y_true: List[float],
    y_pred: List[float],
    sample_size: int = 300,
) -> Dict[str, Any]:
    """Generates regression residual plot (Predicted vs Residual)."""
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    residuals = y_true_arr - y_pred_arr

    if len(y_pred_arr) > sample_size:
        idx = np.random.choice(len(y_pred_arr), sample_size, replace=False)
        y_pred_arr = y_pred_arr[idx]
        residuals = residuals[idx]

    return {
        "plot_type": "residuals_plot",
        "predicted": [round(float(p), 3) for p in y_pred_arr],
        "residuals": [round(float(r), 3) for r in residuals],
    }
