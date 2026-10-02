"""
DataWise AI — Profiling Tools Package
"""

from .schema import extract_schema
from .statistics import compute_column_statistics
from .cardinality import analyze_cardinality
from .distributions import analyze_feature_distributions
import pandas as pd
from typing import Any, Dict


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs complete profiling suite combining schema, statistics, cardinality, and distributions."""
    schema_res = extract_schema(df)
    stats_res = compute_column_statistics(df)
    card_res = analyze_cardinality(df)
    dist_res = analyze_feature_distributions(df)

    return {
        "schema": schema_res,
        "statistics": stats_res,
        "cardinality": card_res,
        "distributions": dist_res,
        "summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            "numeric_count": len(schema_res["numerical_columns"]),
            "categorical_count": len(schema_res["categorical_columns"]),
            "datetime_count": len(schema_res["datetime_columns"]),
        },
    }

__all__ = [
    "extract_schema",
    "compute_column_statistics",
    "analyze_cardinality",
    "analyze_feature_distributions",
    "profile_dataset",
]
