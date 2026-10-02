"""
DataWise AI — Evaluation & Explainability Tools
Deterministic metrics computation, cross-validation evaluation, overfitting detection, SHAP explainability, and robustness checks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, mean_squared_error, r2_score, mean_absolute_error
from app.tools.model_evaluator import ModelEvaluator


def evaluate_classification_model(y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None) -> Dict[str, float]:
    """Computes deterministic classification metrics."""
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "precision": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
    }


def evaluate_regression_model(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes deterministic regression metrics."""
    return {
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "r2_score": round(float(r2_score(y_true, y_pred)), 4),
    }


def detect_overfitting_underfitting(train_score: float, test_score: float, threshold: float = 0.10) -> Dict[str, Any]:
    gap = train_score - test_score
    is_overfit = bool(gap > threshold)
    is_underfit = bool(test_score < 0.60)
    return {
        "generalization_gap": round(gap, 4),
        "is_overfitting": is_overfit,
        "is_underfitting": is_underfit,
        "diagnosis": "overfitting" if is_overfit else ("underfitting" if is_underfit else "good_fit")
    }


def calculate_fairness_disparity(selection_rate_protected: float, selection_rate_reference: float) -> float:
    if selection_rate_reference == 0:
        return 1.0
    return round(float(selection_rate_protected / selection_rate_reference), 4)


def compute_robustness_metrics(clean_score: float, corrupted_score: float) -> Dict[str, Any]:
    drop = clean_score - corrupted_score
    return {
        "clean_metric": clean_score,
        "corrupted_metric": corrupted_score,
        "performance_degradation": round(drop, 4),
        "is_robust": bool(drop < 0.15)
    }


__all__ = [
    "ModelEvaluator",
    "evaluate_classification_model",
    "evaluate_regression_model",
    "detect_overfitting_underfitting",
    "calculate_fairness_disparity",
    "compute_robustness_metrics",
]
