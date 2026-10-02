"""
DataWise AI — Outliers: Standard Z-Score Method
"""

from typing import Any, Dict
import numpy as np
import pandas as pd


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> Dict[str, Any]:
    """Detects outliers exceeding standard deviation threshold from mean."""
    clean = series.dropna()
    if len(clean) < 4:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "threshold": threshold, "indices": []}

    mean_val = clean.mean()
    std_val = clean.std()
    if std_val == 0 or np.isnan(std_val):
        return {"outlier_count": 0, "outlier_percentage": 0.0, "threshold": threshold, "indices": []}

    z_scores = np.abs((clean - mean_val) / std_val)
    mask = z_scores > threshold
    outlier_indices = clean[mask].index.tolist()

    return {
        "method": "Z-score",
        "threshold": threshold,
        "mean": round(float(mean_val), 4),
        "std": round(float(std_val), 4),
        "outlier_count": int(mask.sum()),
        "outlier_percentage": round((mask.sum() / len(clean)) * 100, 2),
        "indices": outlier_indices[:100],
    }
