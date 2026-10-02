"""
DataWise AI — Outliers: Local Outlier Factor (LOF)
"""

from typing import Any, Dict
import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor


def detect_outliers_lof(
    df: pd.DataFrame,
    n_neighbors: int = 20,
    contamination: float = 0.05,
) -> Dict[str, Any]:
    """Density-based local outlier detection for clustering and manifold structures."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df) <= n_neighbors or len(numeric_df.columns) < 2:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "indices": [], "note": "Insufficient points for LOF neighbors"}

    lof = LocalOutlierFactor(
        n_neighbors=min(n_neighbors, len(numeric_df) - 1),
        contamination=contamination,
        n_jobs=-1,
    )
    preds = lof.fit_predict(numeric_df)
    outlier_mask = preds == -1
    outlier_indices = numeric_df.index[outlier_mask].tolist()

    return {
        "method": "Local Outlier Factor (LOF)",
        "n_neighbors": n_neighbors,
        "total_evaluated": len(numeric_df),
        "outlier_count": int(outlier_mask.sum()),
        "outlier_percentage": round((outlier_mask.sum() / len(numeric_df)) * 100, 2),
        "indices": outlier_indices[:100],
    }
