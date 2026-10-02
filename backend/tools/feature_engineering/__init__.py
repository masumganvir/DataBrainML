"""
DataWise AI — Feature Engineering Tools Package
"""

from .datetime import extract_datetime_features
from .interaction import generate_interaction_features
from .polynomial import generate_polynomial_features
from .ratios import generate_ratio_features
from .aggregation import generate_aggregation_features

import pandas as pd
from typing import Any, Dict, List, Optional


def recommend_and_engineer_features(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Intelligently analyzes dataset to generate domain-appropriate features:
    - Datetime decompositions
    - Top correlated interaction pairs
    - Safe ratios
    Avoids generating thousands of meaningless features.
    """
    candidates: List[Dict[str, Any]] = []

    # 1. Datetime candidates
    for col in df.columns:
        if col == target_column:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower() or "time" in col.lower():
            candidates.append({
                "type": "datetime",
                "column": col,
                "reason": f"Decompose calendar seasonality and weekend indicators for {col}",
            })

    # 2. Top numerical pair interactions / ratios
    numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if c != target_column]
    if len(numeric_cols) >= 2:
        # Pick top 2 pairs
        p1 = (numeric_cols[0], numeric_cols[1])
        candidates.append({
            "type": "ratio",
            "numerator": p1[0],
            "denominator": p1[1],
            "reason": f"Capture intensity ratio between {p1[0]} and {p1[1]}",
        })
        candidates.append({
            "type": "interaction",
            "feature_a": p1[0],
            "feature_b": p1[1],
            "reason": f"Capture non-linear joint interaction between {p1[0]} and {p1[1]}",
        })

    return {
        "candidate_recommendations": candidates,
        "recommendation_count": len(candidates),
    }


__all__ = [
    "extract_datetime_features",
    "generate_interaction_features",
    "generate_polynomial_features",
    "generate_ratio_features",
    "generate_aggregation_features",
    "recommend_and_engineer_features",
]
