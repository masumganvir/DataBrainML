"""
DataWise AI — Visualization: Outlier Boxplot & Scatter Specs
"""

from typing import Any, Dict
import pandas as pd


def generate_outlier_plot_spec(series: pd.Series) -> Dict[str, Any]:
    """Generates boxplot coordinates with explicit outlier markers."""
    clean = series.dropna()
    if len(clean) == 0:
        return {"plot_type": "outlier_boxplot", "feature": series.name, "outliers": []}

    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = clean[(clean < lower) | (clean > upper)].tolist()

    return {
        "plot_type": "outlier_boxplot",
        "feature": series.name,
        "q1": round(q1, 3),
        "median": round(float(clean.median()), 3),
        "q3": round(q3, 3),
        "lower_whisker": round(lower, 3),
        "upper_whisker": round(upper, 3),
        "outlier_values": outliers[:50],
        "outlier_count": len(outliers),
    }
