"""
DataWise AI — Visualization: Time Series Trends & Rolling Stats
"""

from typing import Any, Dict
import pandas as pd


def generate_time_series_spec(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    window: int = 7,
) -> Dict[str, Any]:
    """Generates time-ordered line plot and rolling mean trends."""
    sub = df[[date_col, value_col]].dropna().copy()
    sub[date_col] = pd.to_datetime(sub[date_col])
    sub = sub.sort_values(date_col)

    sub["rolling_mean"] = sub[value_col].rolling(window=window, min_periods=1).mean()

    # Downsample if too large for web charts
    if len(sub) > 500:
        step = len(sub) // 300
        sub = sub.iloc[::step]

    dates = [d.strftime("%Y-%m-%d") for d in sub[date_col]]
    values = [round(float(v), 3) for v in sub[value_col]]
    rolling = [round(float(v), 3) for v in sub["rolling_mean"]]

    return {
        "plot_type": "time_series_line",
        "date_column": date_col,
        "value_column": value_col,
        "dates": dates,
        "values": values,
        "rolling_mean": rolling,
        "window": window,
    }
