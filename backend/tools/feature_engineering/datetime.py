"""
DataWise AI — Feature Engineering: Datetime Decomposition
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def extract_datetime_features(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Decomposes datetime columns into cyclical and calendar features."""
    dt_series = pd.to_datetime(df[col], errors="coerce")
    engineered = pd.DataFrame(index=df.index)
    meta: List[Dict[str, Any]] = []

    prefix = f"{col}_"

    engineered[f"{prefix}year"] = dt_series.dt.year
    meta.append({"name": f"{prefix}year", "formula": f"{col}.year", "reason": "Captures long-term annual drift/trend"})

    engineered[f"{prefix}month"] = dt_series.dt.month
    meta.append({"name": f"{prefix}month", "formula": f"{col}.month", "reason": "Captures seasonality across months"})

    engineered[f"{prefix}day"] = dt_series.dt.day
    meta.append({"name": f"{prefix}day", "formula": f"{col}.day", "reason": "Captures monthly cycle day"})

    engineered[f"{prefix}dayofweek"] = dt_series.dt.dayofweek
    meta.append({"name": f"{prefix}dayofweek", "formula": f"{col}.dayofweek", "reason": "Captures weekly cyclic variations"})

    engineered[f"{prefix}is_weekend"] = dt_series.dt.dayofweek.isin([5, 6]).astype(int)
    meta.append({"name": f"{prefix}is_weekend", "formula": f"{col}.dayofweek in [5,6]", "reason": "Identifies weekend behavior distinct from weekdays"})

    if dt_series.dt.hour.nunique() > 1:
        engineered[f"{prefix}hour"] = dt_series.dt.hour
        meta.append({"name": f"{prefix}hour", "formula": f"{col}.hour", "reason": "Captures intraday hourly patterns"})

    return engineered, meta
