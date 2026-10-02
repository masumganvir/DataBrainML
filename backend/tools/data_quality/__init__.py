"""
DataWise AI — Data Quality Tools Package
"""

from .missing import detect_missing_values
from .duplicates import detect_duplicates
from .invalid_values import detect_invalid_values
from .consistency import check_consistency
import pandas as pd
from typing import Any, Dict


def audit_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Runs end-to-end data quality audit without mutating original data."""
    missing_res = detect_missing_values(df)
    duplicates_res = detect_duplicates(df)
    invalid_res = detect_invalid_values(df)
    consistency_res = check_consistency(df)

    # Compute overall quality score (0-100)
    score = 100.0
    if missing_res["missing_columns_count"] > 0:
        score -= min(missing_res["missing_columns_count"] * 5.0, 30.0)
    if duplicates_res["duplicate_rows_pct"] > 0:
        score -= min(duplicates_res["duplicate_rows_pct"] * 2.0, 20.0)
    if invalid_res["issue_count"] > 0:
        score -= min(invalid_res["issue_count"] * 5.0, 25.0)
    if consistency_res["has_consistency_issues"]:
        score -= 10.0

    return {
        "quality_score": max(round(score, 1), 0.0),
        "missing_analysis": missing_res,
        "duplicate_analysis": duplicates_res,
        "invalid_value_analysis": invalid_res,
        "consistency_analysis": consistency_res,
    }


__all__ = [
    "detect_missing_values",
    "detect_duplicates",
    "detect_invalid_values",
    "check_consistency",
    "audit_data_quality",
]
