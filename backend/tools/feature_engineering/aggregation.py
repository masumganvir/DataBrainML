"""
DataWise AI — Feature Engineering: Grouped Aggregations
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def generate_aggregation_features(
    df: pd.DataFrame,
    group_col: str,
    agg_col: str,
    funcs: List[str] = None,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Generates group-level mean, std, or count transformations mapped back to observation rows."""
    if funcs is None:
        funcs = ["mean", "std"]

    engineered = pd.DataFrame(index=df.index)
    meta: List[Dict[str, Any]] = []

    for fn in funcs:
        feat_name = f"{group_col}_{agg_col}_{fn}"
        grouped = df.groupby(group_col)[agg_col].transform(fn)
        engineered[feat_name] = grouped
        meta.append({
            "name": feat_name,
            "formula": f"df.groupby('{group_col}')['{agg_col}'].transform('{fn}')",
            "reason": f"Contextualizes individual {agg_col} relative to cohort {group_col} benchmark.",
            "expected_benefit": "Enables detection of deviations from group norms.",
        })

    return engineered, meta
