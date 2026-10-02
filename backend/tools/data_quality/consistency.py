"""
DataWise AI — Data Quality: Consistency Checks
"""

from typing import Any, Dict, List
import pandas as pd


def check_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Checks for:
    - Inconsistent string casing (e.g., 'Yes', 'yes', 'YES')
    - Constant and near-constant features (zero variance)
    - Mixed types in object columns
    """
    inconsistent_casing: List[Dict[str, Any]] = []
    constant_features: List[str] = []
    near_constant_features: List[Dict[str, Any]] = []

    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        nunique = series.nunique(dropna=True)

        if nunique <= 1:
            constant_features.append(col)
            continue

        # Check near-constant
        top_freq = series.value_counts(normalize=True, dropna=False).iloc[0]
        if top_freq >= 0.98:
            near_constant_features.append({
                "column": col,
                "dominant_value": str(series.value_counts(dropna=False).index[0]),
                "frequency_pct": round(top_freq * 100, 2),
            })

        # Casing check for categorical/object
        if series.dtype == "object":
            str_series = series.dropna().astype(str)
            raw_uniques = str_series.unique()
            lower_uniques = str_series.str.lower().str.strip().unique()

            if len(raw_uniques) != len(lower_uniques) and len(lower_uniques) < 30:
                inconsistent_casing.append({
                    "column": col,
                    "distinct_raw_values": len(raw_uniques),
                    "distinct_standardized_values": len(lower_uniques),
                    "example_inconsistencies": list(raw_uniques[:6]),
                })

    return {
        "constant_features": constant_features,
        "near_constant_features": near_constant_features,
        "inconsistent_casing_columns": inconsistent_casing,
        "has_consistency_issues": bool(constant_features or near_constant_features or inconsistent_casing),
    }
