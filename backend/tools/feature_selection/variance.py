"""
DataWise AI — Feature Selection: Variance Thresholding
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
from sklearn.feature_selection import VarianceThreshold


def filter_low_variance(
    df: pd.DataFrame,
    threshold: float = 0.01,
) -> Dict[str, Any]:
    """Identifies and filters constant and near-constant numerical features."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df.columns) == 0:
        return {"kept_features": list(df.columns), "dropped_features": []}

    selector = VarianceThreshold(threshold=threshold)
    selector.fit(numeric_df)

    kept = list(numeric_df.columns[selector.get_support()])
    dropped = [c for c in numeric_df.columns if c not in kept]

    return {
        "method": "VarianceThreshold",
        "threshold": threshold,
        "kept_features": kept,
        "dropped_features": dropped,
        "dropped_count": len(dropped),
    }
