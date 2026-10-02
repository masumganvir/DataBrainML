"""
DataWise AI — Visualization: Correlation Heatmaps
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def generate_correlation_matrix_spec(df: pd.DataFrame, method: str = "pearson") -> Dict[str, Any]:
    """Generates correlation matrix and top correlated pairs."""
    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) < 2:
        return {"plot_type": "correlation_heatmap", "columns": [], "matrix": [], "top_pairs": []}

    corr = numeric_df.corr(method=method).round(3)
    cols = list(corr.columns)
    matrix = corr.values.tolist()

    # Find top pairs
    top_pairs: List[Dict[str, Any]] = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if not np.isnan(val):
                top_pairs.append({
                    "feature_a": cols[i],
                    "feature_b": cols[j],
                    "correlation": float(val),
                    "abs_correlation": abs(float(val)),
                })

    top_pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)

    return {
        "plot_type": "correlation_heatmap",
        "method": method,
        "columns": cols,
        "matrix": matrix,
        "top_pairs": top_pairs[:15],
    }
