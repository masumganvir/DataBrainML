"""
DataWise AI — Outliers: Modified Z-Score (MAD) Method
"""

from typing import Any, Dict
import numpy as np
import pandas as pd


def detect_outliers_modified_zscore(series: pd.Series, threshold: float = 3.5) -> Dict[str, Any]:
    """Detects outliers using Median Absolute Deviation (Boris Iglewicz and David Hoaglin formula)."""
    clean = series.dropna()
    if len(clean) < 4:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "threshold": threshold, "indices": []}

    med = np.median(clean)
    abs_dev = np.abs(clean - med)
    mad = np.median(abs_dev)

    if mad == 0:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "threshold": threshold, "indices": []}

    mod_z = 0.6745 * abs_dev / mad
    mask = mod_z > threshold
    outlier_indices = clean[mask].index.tolist()

    return {
        "method": "Modified Z-score (MAD)",
        "threshold": threshold,
        "median": round(float(med), 4),
        "mad": round(float(mad), 4),
        "outlier_count": int(mask.sum()),
        "outlier_percentage": round((mask.sum() / len(clean)) * 100, 2),
        "indices": outlier_indices[:100],
    }
