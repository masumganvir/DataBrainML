"""
Agentic AutoML Intelligence Platform — Real-Time Drift Detection Engine
Computes Population Stability Index (PSI), KS-test, Wasserstein, and Concept Drift.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """Calculate Population Stability Index (PSI) between reference and current feature distributions."""
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Clean NaNs and infs
    clean_expected = expected[np.isfinite(expected)]
    clean_actual = actual[np.isfinite(actual)]

    if len(clean_expected) < 10 or len(clean_actual) < 10:
        return 0.0

    # Determine quantile bins based on reference distribution
    try:
        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(clean_expected, quantiles)
        bins[0] = -np.inf
        bins[-1] = np.inf
        bins = np.unique(bins)
    except Exception:
        return 0.0

    if len(bins) < 2:
        return 0.0

    expected_counts, _ = np.histogram(clean_expected, bins=bins)
    actual_counts, _ = np.histogram(clean_actual, bins=bins)

    expected_pct = expected_counts / len(clean_expected)
    actual_pct = actual_counts / len(clean_actual)

    # Apply epsilon smoothing
    expected_pct = np.clip(expected_pct, epsilon, 1.0)
    actual_pct = np.clip(actual_pct, epsilon, 1.0)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(np.nan_to_num(psi_val, nan=0.0, posinf=1.0, neginf=0.0))


class DriftDetectionEngine:
    """Enterprise statistical engine for continuous drift detection."""

    PSI_THRESHOLD_STABLE = 0.10
    PSI_THRESHOLD_MODERATE = 0.20

    @classmethod
    def compute_numerical_feature_drift(
        cls,
        baseline_series: pd.Series,
        current_series: pd.Series,
    ) -> Dict[str, Any]:
        """Compute PSI and KS-test for a numeric feature."""
        base_clean = pd.to_numeric(baseline_series, errors="coerce").dropna().values
        curr_clean = pd.to_numeric(current_series, errors="coerce").dropna().values

        if len(base_clean) < 10 or len(curr_clean) < 10:
            return {
                "drift_detected": False,
                "psi": 0.0,
                "ks_p_value": 1.0,
                "severity": "none",
                "message": "Insufficient data points for drift calculation.",
            }

        psi = calculate_psi(base_clean, curr_clean)
        ks_stat, ks_p_val = stats.ks_2samp(base_clean, curr_clean)

        severity = "low"
        drift_detected = False

        if psi > cls.PSI_THRESHOLD_MODERATE or ks_p_val < 0.01:
            severity = "high"
            drift_detected = True
        elif psi > cls.PSI_THRESHOLD_STABLE or ks_p_val < 0.05:
            severity = "medium"
            drift_detected = True

        return {
            "drift_detected": drift_detected,
            "psi": round(psi, 4),
            "ks_statistic": round(float(ks_stat), 4),
            "ks_p_value": round(float(ks_p_val), 4),
            "severity": severity,
            "mean_shift": round(float(np.mean(curr_clean) - np.mean(base_clean)), 4),
        }

    @classmethod
    def compute_categorical_feature_drift(
        cls,
        baseline_series: pd.Series,
        current_series: pd.Series,
    ) -> Dict[str, Any]:
        """Compute categorical frequency distribution divergence."""
        base_counts = baseline_series.astype(str).value_counts(normalize=True)
        curr_counts = current_series.astype(str).value_counts(normalize=True)

        all_cats = set(base_counts.index).union(set(curr_counts.index))
        p = np.array([base_counts.get(c, 1e-4) for c in all_cats])
        q = np.array([curr_counts.get(c, 1e-4) for c in all_cats])

        p /= p.sum()
        q /= q.sum()

        # Total Variation Distance
        tvd = float(0.5 * np.sum(np.abs(p - q)))
        drift_detected = tvd > 0.15
        severity = "high" if tvd > 0.25 else ("medium" if tvd > 0.15 else "low")

        return {
            "drift_detected": drift_detected,
            "total_variation_distance": round(tvd, 4),
            "severity": severity,
            "new_categories_detected": list(set(curr_counts.index) - set(base_counts.index)),
        }

    @classmethod
    def compute_dataset_drift(
        cls,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Evaluate full dataset covariate drift across all features."""
        feature_results = {}
        drifted_features = []
        high_severity_count = 0

        common_cols = [c for c in baseline_df.columns if c in current_df.columns]

        for col in common_cols:
            if pd.api.types.is_numeric_dtype(baseline_df[col]):
                res = cls.compute_numerical_feature_drift(baseline_df[col], current_df[col])
            else:
                res = cls.compute_categorical_feature_drift(baseline_df[col], current_df[col])

            feature_results[col] = res
            if res["drift_detected"]:
                drifted_features.append(col)
                if res["severity"] == "high":
                    high_severity_count += 1

        overall_drift_ratio = len(drifted_features) / len(common_cols) if common_cols else 0.0
        overall_severity = "none"
        if high_severity_count > 0 or overall_drift_ratio > 0.3:
            overall_severity = "high"
        elif overall_drift_ratio > 0.15:
            overall_severity = "medium"
        elif overall_drift_ratio > 0:
            overall_severity = "low"

        return {
            "drift_detected": overall_drift_ratio > 0.15 or high_severity_count > 0,
            "overall_severity": overall_severity,
            "drift_ratio": round(overall_drift_ratio, 3),
            "drifted_features_count": len(drifted_features),
            "total_features_evaluated": len(common_cols),
            "drifted_features": drifted_features,
            "feature_details": feature_results,
        }

    @classmethod
    def compute_concept_drift(
        cls,
        predictions: np.ndarray,
        ground_truth: np.ndarray,
        baseline_metric_value: float,
        metric_name: str = "f1",
        problem_type: str = "classification",
    ) -> Dict[str, Any]:
        """Assess concept drift when real ground truth arrives asynchronously."""
        from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score

        if len(predictions) == 0 or len(ground_truth) == 0:
            return {"concept_drift_detected": False, "message": "No ground truth available yet."}

        if problem_type == "classification":
            current_metric = float(f1_score(ground_truth, predictions, average="weighted", zero_division=0))
            degradation = baseline_metric_value - current_metric
        else:
            current_metric = float(mean_squared_error(ground_truth, predictions, squared=False))
            degradation = current_metric - baseline_metric_value  # for RMSE, higher is worse

        drift_detected = degradation > 0.10
        severity = "high" if degradation > 0.20 else ("medium" if degradation > 0.10 else "low")

        return {
            "concept_drift_detected": drift_detected,
            "metric_name": metric_name,
            "baseline_metric": round(baseline_metric_value, 4),
            "current_production_metric": round(current_metric, 4),
            "performance_degradation": round(float(degradation), 4),
            "severity": severity,
            "sample_size": len(ground_truth),
        }


drift_engine = DriftDetectionEngine()
