"""
DataWise AI — Outlier Intelligence Tools Package
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from .iqr import detect_outliers_iqr
from .zscore import detect_outliers_zscore
from .modified_zscore import detect_outliers_modified_zscore
from .isolation_forest import detect_outliers_isolation_forest
from .lof import detect_outliers_lof


def analyze_all_outliers(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    task_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes outliers across univariate and multivariate methods.
    Applies context-aware reasoning to recommend:
    KEEP, REMOVE, CAP, WINSORIZE, TRANSFORM, or INVESTIGATE.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    feature_reports: Dict[str, Any] = {}

    for col in numeric_cols:
        if col == target_column:
            continue
        series = df[col]
        iqr_res = detect_outliers_iqr(series)
        z_res = detect_outliers_zscore(series)
        mad_res = detect_outliers_modified_zscore(series)

        # Context-aware recommendation
        col_lower = col.lower()
        is_fraud_like = any(k in col_lower for k in ["amount", "transaction", "fraud", "claim", "loss", "anomaly"])
        outlier_pct = iqr_res["outlier_percentage"]

        if is_fraud_like:
            rec = "KEEP"
            reason = "Feature appears transaction/loss related; rare extreme values often carry critical fraud/signal value."
        elif outlier_pct > 15.0:
            rec = "TRANSFORM"
            reason = "High percentage of statistical outliers indicates severe distribution skew. Apply log1p or Yeo-Johnson."
        elif outlier_pct > 3.0:
            rec = "WINSORIZE"
            reason = "Moderate outlier percentage; winsorization caps extreme tail influence without discarding observations."
        elif outlier_pct > 0.0:
            rec = "CAP"
            reason = "Mild outliers detected; clip to 1.5*IQR bounds during preprocessing."
        else:
            rec = "KEEP"
            reason = "No significant outliers detected."

        feature_reports[col] = {
            "iqr": iqr_res,
            "zscore": z_res,
            "modified_zscore": mad_res,
            "recommended_decision": rec,
            "rationale": reason,
        }

    # Multivariate check
    multivariate_res = detect_outliers_isolation_forest(df)

    return {
        "features": feature_reports,
        "multivariate": multivariate_res,
        "features_with_outliers_count": sum(
            1 for v in feature_reports.values() if v["iqr"]["outlier_count"] > 0
        ),
    }


__all__ = [
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "detect_outliers_modified_zscore",
    "detect_outliers_isolation_forest",
    "detect_outliers_lof",
    "analyze_all_outliers",
]
