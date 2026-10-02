"""
DataWise AI — Visualization: Distribution Plots (Histograms, KDE, Box Plots)
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def generate_distribution_spec(series: pd.Series, bins: int = 25) -> Dict[str, Any]:
    """Generates compact binned histogram and boxplot coordinates for frontend charts."""
    clean = series.dropna()
    if len(clean) == 0:
        return {"plot_type": "histogram", "bins": [], "counts": []}

    counts, bin_edges = np.histogram(clean, bins=bins)
    bin_labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]

    return {
        "plot_type": "histogram_kde",
        "feature": series.name,
        "bins": bin_labels,
        "counts": [int(c) for c in counts],
        "min": round(float(clean.min()), 4),
        "max": round(float(clean.max()), 4),
        "median": round(float(clean.median()), 4),
        "q1": round(float(clean.quantile(0.25)), 4),
        "q3": round(float(clean.quantile(0.75)), 4),
    }
