"""
DataWise AI — Leakage: Target Leakage Detection
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def detect_target_leakage(
    df: pd.DataFrame,
    target_column: str,
    threshold: float = 0.95,
) -> Dict[str, Any]:
    """Detects features that suspiciously predict or correlate near-perfectly with the target."""
    if target_column not in df.columns:
        return {"leaked_features": [], "status": "target_missing"}

    leaked: List[Dict[str, Any]] = []
    target = df[target_column]

    for col in df.columns:
        if col == target_column:
            continue
        series = df[col]

        # 1. Exact equality / duplicate of target
        if series.equals(target):
            leaked.append({
                "feature": col,
                "reason": "Exact duplicate of target column",
                "severity": "CRITICAL",
                "block_pipeline": True,
            })
            continue

        # 2. Perfect correlation for numeric
        if pd.api.types.is_numeric_dtype(series) and pd.api.types.is_numeric_dtype(target):
            valid = df[[col, target_column]].dropna()
            if len(valid) > 10:
                corr = abs(float(valid.corr().iloc[0, 1]))
                if corr >= threshold:
                    leaked.append({
                        "feature": col,
                        "correlation": round(corr, 4),
                        "reason": f"Near-perfect correlation ({corr:.3f}) with target. Likely a post-outcome variable or proxy.",
                        "severity": "CRITICAL",
                        "block_pipeline": True,
                    })

        # 3. Post-outcome keyword check
        col_lower = col.lower()
        if any(w in col_lower for w in ["churn_date", "discharge_status", "death_date", "outcome", "post_event"]):
            leaked.append({
                "feature": col,
                "reason": "Column name implies post-outcome measurement after event took place.",
                "severity": "HIGH",
                "block_pipeline": True,
            })

    return {
        "leaked_features": leaked,
        "has_target_leakage": len(leaked) > 0,
        "should_block_pipeline": any(item.get("block_pipeline") for item in leaked),
    }
