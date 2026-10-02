"""
DataWise AI — Visualization: Categorical Frequency Plots
"""

from typing import Any, Dict
import pandas as pd


def generate_categorical_spec(series: pd.Series, top_k: int = 15) -> Dict[str, Any]:
    """Generates categorical count and frequency specifications."""
    vc = series.value_counts(dropna=False).head(top_k)
    categories = [str(k) if pd.notnull(k) else "Missing/Null" for k in vc.index]
    counts = [int(v) for v in vc.values]
    percentages = [round((v / len(series)) * 100, 2) for v in vc.values]

    return {
        "plot_type": "categorical_bar",
        "feature": series.name,
        "categories": categories,
        "counts": counts,
        "percentages": percentages,
        "total_unique": int(series.nunique(dropna=False)),
    }
