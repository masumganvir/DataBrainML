"""
DataWise AI — Outliers: Isolation Forest Multivariate Detection
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_outliers_isolation_forest(
    df: pd.DataFrame,
    contamination: float = 0.05,
    random_state: int = 42,
) -> Dict[str, Any]:
    """Detects multivariate anomalies using tree partitioning depth."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df) < 20 or len(numeric_df.columns) < 2:
        return {"outlier_count": 0, "outlier_percentage": 0.0, "indices": [], "note": "Insufficient numeric dimensions/rows"}

    iso = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
        n_jobs=-1,
    )
    preds = iso.fit_predict(numeric_df)
    scores = iso.decision_function(numeric_df)

    outlier_mask = preds == -1
    outlier_indices = numeric_df.index[outlier_mask].tolist()

    return {
        "method": "Isolation Forest",
        "contamination": contamination,
        "features_used": list(numeric_df.columns),
        "total_evaluated": len(numeric_df),
        "outlier_count": int(outlier_mask.sum()),
        "outlier_percentage": round((outlier_mask.sum() / len(numeric_df)) * 100, 2),
        "anomaly_score_mean": round(float(scores[outlier_mask].mean()), 4) if outlier_mask.sum() > 0 else 0.0,
        "indices": outlier_indices[:100],
    }
