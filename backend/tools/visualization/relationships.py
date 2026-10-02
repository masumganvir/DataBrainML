"""
DataWise AI — Visualization: Feature Relationships (Scatter & Grouped Plots)
"""

from typing import Any, Dict
import pandas as pd


def generate_scatter_spec(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    hue_col: str = None,
    sample_size: int = 400,
) -> Dict[str, Any]:
    """Generates downsampled scatter plot data points for responsive UI rendering."""
    cols = [x_col, y_col] + ([hue_col] if hue_col else [])
    sub = df[cols].dropna()

    if len(sub) > sample_size:
        sub = sub.sample(sample_size, random_state=42)

    points = []
    for _, row in sub.iterrows():
        pt = {"x": round(float(row[x_col]), 4), "y": round(float(row[y_col]), 4)}
        if hue_col:
            pt["hue"] = str(row[hue_col])
        points.append(pt)

    return {
        "plot_type": "scatter_plot",
        "x_label": x_col,
        "y_label": y_col,
        "hue_label": hue_col,
        "points": points,
        "total_points": len(points),
    }
