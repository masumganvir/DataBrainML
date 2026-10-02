"""
DataWise AI — Profiling: Cardinality Analysis
"""

from typing import Any, Dict, List
import pandas as pd


def analyze_cardinality(df: pd.DataFrame) -> Dict[str, Any]:
    """Evaluates cardinality levels and recommends encoding strategies."""
    n_rows = len(df)
    low_cardinality: List[Dict[str, Any]] = []
    medium_cardinality: List[Dict[str, Any]] = []
    high_cardinality: List[Dict[str, Any]] = []
    identifiers: List[str] = []

    for col in df.columns:
        series = df[col]
        unique_cnt = int(series.nunique(dropna=True))
        unique_ratio = unique_cnt / max(n_rows, 1)

        info = {
            "column": col,
            "unique_count": unique_cnt,
            "unique_ratio": round(unique_ratio, 4),
            "dtype": str(series.dtype),
        }

        if unique_ratio > 0.85 and n_rows > 30 and not pd.api.types.is_numeric_dtype(series):
            identifiers.append(col)
        elif unique_cnt <= 10:
            info["recommended_encoding"] = "OneHotEncoder"
            low_cardinality.append(info)
        elif unique_cnt <= 50:
            info["recommended_encoding"] = "OrdinalEncoder / TargetEncoder"
            medium_cardinality.append(info)
        else:
            info["recommended_encoding"] = "TargetEncoder / FrequencyEncoder / Embeddings"
            high_cardinality.append(info)

    return {
        "low_cardinality": low_cardinality,
        "medium_cardinality": medium_cardinality,
        "high_cardinality": high_cardinality,
        "potential_identifiers": identifiers,
        "total_columns_evaluated": len(df.columns),
    }
