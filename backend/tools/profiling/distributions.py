"""
DataWise AI — Profiling: Distribution Shape Analysis
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from scipy import stats


def analyze_feature_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes distribution skewness, kurtosis, and recommended mathematical transformations."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    distribution_reports = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 8:
            continue

        skew_val = float(stats.skew(series))
        kurt_val = float(stats.kurtosis(series))

        # Check normality via shapiro on small sample or jarque-bera
        sample = series.sample(min(len(series), 500), random_state=42)
        try:
            stat, p_val = stats.shapiro(sample)
            is_normal = p_val > 0.05
        except Exception:
            is_normal = abs(skew_val) < 0.5

        # Recommendation
        if abs(skew_val) < 0.5:
            shape = "symmetric"
            transform = "None (StandardScaler)"
        elif skew_val >= 1.0:
            shape = "highly_right_skewed"
            transform = "log1p" if (series >= 0).all() else "Yeo-Johnson"
        elif skew_val <= -1.0:
            shape = "highly_left_skewed"
            transform = "Yeo-Johnson"
        else:
            shape = "moderately_skewed"
            transform = "RobustScaler"

        distribution_reports[col] = {
            "skewness": round(skew_val, 4),
            "kurtosis": round(kurt_val, 4),
            "distribution_shape": shape,
            "is_approximately_normal": is_normal,
            "recommended_transformation": transform,
        }

    return {
        "distributions": distribution_reports,
        "skewed_features_count": sum(
            1 for v in distribution_reports.values() if abs(v["skewness"]) >= 1.0
        ),
    }
