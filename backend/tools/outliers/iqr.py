"""
DataWise AI — Outliers: IQR (Interquartile Range) Method
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def detect_outliers_iqr(series: pd.Series, multiplier: float = 1.5) -> Dict[str, Any]:
    """Detects univariate outliers using Tukey's IQR rule."""
    clean = series.dropna()
    if len(clean) < 4:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "lower_bound": None, "upper_bound": None, "indices": []}

    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1

    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    mask = (clean < lower_bound) | (clean > upper_bound)
    outlier_indices = clean[mask].index.tolist()
    outlier_values = clean[mask].tolist()

    return {
        "method": "IQR",
        "multiplier": multiplier,
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "lower_bound": round(lower_bound, 4),
        "upper_bound": round(upper_bound, 4),
        "outlier_count": int(mask.sum()),
        "outlier_percentage": round((mask.sum() / len(clean)) * 100, 2),
        "indices": outlier_indices[:100],  # compact
        "sample_outliers": outlier_values[:10],
    }
