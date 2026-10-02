"""
DataWise AI — Data Quality: Missing Value Diagnostics
"""

from typing import Any, Dict, List
import pandas as pd


def detect_missing_values(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes missingness per column, missing rates, and severity levels."""
    n_rows = len(df)
    missing_cols: List[Dict[str, Any]] = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        if null_count > 0:
            null_pct = round((null_count / max(n_rows, 1)) * 100, 2)
            if null_pct < 5.0:
                severity = "LOW"
                rec = "median/mean (numerical) or mode (categorical)"
            elif null_pct < 20.0:
                severity = "MEDIUM"
                rec = "KNNImputer or IterativeImputer"
            elif null_pct < 60.0:
                severity = "HIGH"
                rec = "Indicator column + Model imputation"
            else:
                severity = "CRITICAL"
                rec = "Consider dropping feature unless business critical"

            missing_cols.append({
                "column": col,
                "missing_count": null_count,
                "missing_pct": null_pct,
                "dtype": str(series.dtype),
                "severity": severity,
                "recommended_action": rec,
            })

    # Sort descending by missing percentage
    missing_cols.sort(key=lambda x: x["missing_pct"], reverse=True)

    return {
        "missing_columns_count": len(missing_cols),
        "total_columns": len(df.columns),
        "columns_with_missing": missing_cols,
        "clean_columns_count": len(df.columns) - len(missing_cols),
    }
