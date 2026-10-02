"""
DataWise AI — Leakage: Temporal Information Leakage
"""

from typing import Any, Dict, List
import pandas as pd


def detect_temporal_leakage(
    df: pd.DataFrame,
    target_column: str,
    time_column: str = None,
) -> Dict[str, Any]:
    """Detects temporal lookahead leakage and out-of-order event timestamps."""
    if not time_column or time_column not in df.columns:
        return {"has_temporal_leakage": False, "warnings": ["No time column specified."]}

    warnings: List[str] = []
    has_leakage = False

    try:
        times = pd.to_datetime(df[time_column], errors="coerce")
        if times.isnull().sum() > 0:
            warnings.append(f"Time column '{time_column}' has unparseable null timestamps.")

        # Check chronological ordering
        if not times.is_monotonic_increasing:
            warnings.append(f"Dataset is not monotonically sorted in time order along '{time_column}'. Random train/test split will leak future records into training set.")
            has_leakage = True
    except Exception as exc:
        warnings.append(f"Failed to check temporal leakage: {exc}")

    return {
        "has_temporal_leakage": has_leakage,
        "warnings": warnings,
        "recommendation": "Use TimeSeriesSplit or chronological train/test split instead of random shuffle.",
    }
