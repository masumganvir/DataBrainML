"""
DataWise AI — Leakage Detection Tools Package
"""

from .target_leakage import detect_target_leakage
from .temporal_leakage import detect_temporal_leakage
from .preprocessing_leakage import verify_pipeline_split_safety

import pandas as pd
from typing import Any, Dict, Optional


def audit_dataset_leakage(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    time_column: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs target, temporal, and methodological leakage audits."""
    if not target_column:
        return {"has_leakage": False, "status": "No target column provided."}

    target_leak = detect_target_leakage(df, target_column)
    temporal_leak = detect_temporal_leakage(df, target_column, time_column)

    has_leakage = target_leak["has_target_leakage"] or temporal_leak["has_temporal_leakage"]

    return {
        "has_leakage": has_leakage,
        "should_block_pipeline": target_leak.get("should_block_pipeline", False),
        "target_leakage": target_leak,
        "temporal_leakage": temporal_leak,
        "leaked_features": [f["feature"] for f in target_leak.get("leaked_features", [])],
    }


__all__ = [
    "detect_target_leakage",
    "detect_temporal_leakage",
    "verify_pipeline_split_safety",
    "audit_dataset_leakage",
]
