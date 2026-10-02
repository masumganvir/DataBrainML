"""
DataWise AI — Feature Selection: Collinearity Filtering
"""

from typing import Any, Dict, List, Set
import numpy as np
import pandas as pd


def filter_collinear_features(
    df: pd.DataFrame,
    threshold: float = 0.85,
) -> Dict[str, Any]:
    """Identifies redundant multi-collinear features and recommends candidates to drop."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df.columns) < 2:
        return {"dropped_features": [], "collinear_pairs": []}

    corr = numeric_df.corr().abs()
    dropped: Set[str] = set()
    pairs: List[Dict[str, Any]] = []

    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            col_a = corr.columns[i]
            col_b = corr.columns[j]
            val = float(corr.iloc[i, j])
            if val >= threshold:
                pairs.append({
                    "feature_1": col_a,
                    "feature_2": col_b,
                    "correlation": round(val, 4),
                })
                # Drop col_b if not already dropped
                if col_a not in dropped:
                    dropped.add(col_b)

    return {
        "method": "Correlation Filtering",
        "threshold": threshold,
        "collinear_pairs": pairs,
        "dropped_features": sorted(list(dropped)),
        "dropped_count": len(dropped),
    }
