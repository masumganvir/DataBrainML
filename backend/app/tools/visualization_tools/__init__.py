"""
DataWise AI — Visualization Tools
Deterministic plot generation, chart recommendations, and interactive visual outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from app.tools.visualization import VisualizationEngine
from app.tools.visualization_planner import plan_visualizations, recommend_plots_for_column
from app.tools.distributions import analyze_distributions, compute_distribution_metrics
from app.tools.correlations import calculate_correlations, find_multicollinear_pairs


def generate_visualization(
    df: pd.DataFrame,
    plot_type: str = "correlation_heatmap",
    columns: Optional[List[str]] = None,
    session_id: str = "default_session"
) -> Dict[str, Any]:
    engine = VisualizationEngine(df, session_id=session_id)
    if plot_type == "correlation_heatmap":
        return engine.plot_correlation_heatmap()
    elif plot_type == "missing_values":
        return engine.plot_missing_values()
    elif plot_type == "distribution" and columns:
        col = columns[0]
        if pd.api.types.is_numeric_dtype(df[col]):
            return engine.plot_numerical_distribution(col)
        else:
            return engine.plot_categorical_distribution(col)
    else:
        # Default to heatmap if numeric cols exist
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) >= 2:
            return engine.plot_correlation_heatmap()
        return {"status": "unsupported_plot_type", "plot_type": plot_type}


def generate_eda_figures(df: pd.DataFrame, session_id: str = "default_session") -> List[Dict[str, Any]]:
    engine = VisualizationEngine(df, session_id=session_id)
    plots = []
    try:
        plots.append(engine.plot_correlation_heatmap())
    except Exception:
        pass
    try:
        plots.append(engine.plot_missing_values())
    except Exception:
        pass
    return plots


__all__ = [
    "VisualizationEngine",
    "generate_visualization",
    "generate_eda_figures",
    "plan_visualizations",
    "recommend_plots_for_column",
    "analyze_distributions",
    "compute_distribution_metrics",
    "calculate_correlations",
    "find_multicollinear_pairs",
]
