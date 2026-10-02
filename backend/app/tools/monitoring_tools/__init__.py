"""
DataWise AI — Monitoring & Drift Detection Tools
Deterministic calculation of Population Stability Index (PSI), Kolmogorov-Smirnov (KS) test,
prediction distribution shifts, and automated retraining evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4
) -> float:
    """
    Computes the Population Stability Index (PSI) between baseline and production distributions.
    PSI < 0.1: No significant change
    0.1 <= PSI < 0.2: Moderate drift detected
    PSI >= 0.2: Significant drift detected, retraining recommended.
    """
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantiles based on baseline expected distribution
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bucket_bounds = np.percentile(expected, percentiles)
    bucket_bounds[0] = -np.inf
    bucket_bounds[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=bucket_bounds)
    actual_counts, _ = np.histogram(actual, bins=bucket_bounds)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    # Avoid zero division
    expected_pct = np.where(expected_pct == 0, epsilon, expected_pct)
    actual_pct = np.where(actual_pct == 0, epsilon, actual_pct)

    psi_value = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(np.round(psi_value, 5))


def calculate_ks_drift(expected: np.ndarray, actual: np.ndarray) -> Dict[str, Any]:
    """
    Performs Kolmogorov-Smirnov 2-sample test for continuous distribution shift.
    """
    if len(expected) == 0 or len(actual) == 0:
        return {"statistic": 0.0, "p_value": 1.0, "drift_detected": False}

    res = stats.ks_2samp(expected, actual)
    drift_detected = bool(res.pvalue < 0.05)
    return {
        "statistic": float(np.round(res.statistic, 5)),
        "p_value": float(np.round(res.pvalue, 5)),
        "drift_detected": drift_detected,
    }


def evaluate_dataset_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    numerical_features: Optional[List[str]] = None,
    psi_threshold: float = 0.2
) -> Dict[str, Any]:
    """
    Evaluates drift across all features and decides if retraining is warranted.
    """
    if numerical_features is None:
        numerical_features = [
            col for col in baseline_df.select_dtypes(include=[np.number]).columns
            if col in current_df.columns
        ]

    feature_drifts: Dict[str, Any] = {}
    drifted_features = []

    for col in numerical_features:
        base_vals = baseline_df[col].dropna().values
        curr_vals = current_df[col].dropna().values

        if len(base_vals) < 5 or len(curr_vals) < 5:
            continue

        psi = calculate_psi(base_vals, curr_vals)
        ks_res = calculate_ks_drift(base_vals, curr_vals)

        is_drifted = (psi >= psi_threshold) or ks_res["drift_detected"]
        if is_drifted:
            drifted_features.append(col)

        feature_drifts[col] = {
            "psi": psi,
            "ks_statistic": ks_res["statistic"],
            "ks_p_value": ks_res["p_value"],
            "drift_detected": is_drifted,
            "drift_severity": "high" if psi >= 0.2 else ("moderate" if psi >= 0.1 else "negligible"),
        }

    drift_ratio = len(drifted_features) / max(1, len(numerical_features))
    retraining_recommended = bool(drift_ratio >= 0.3 or any(f["psi"] >= 0.25 for f in feature_drifts.values()))

    return {
        "features_analyzed": len(numerical_features),
        "drifted_features_count": len(drifted_features),
        "drifted_features": drifted_features,
        "drift_ratio": round(drift_ratio, 4),
        "retraining_recommended": retraining_recommended,
        "feature_details": feature_drifts,
    }


__all__ = [
    "calculate_psi",
    "calculate_ks_drift",
    "evaluate_dataset_drift",
]
