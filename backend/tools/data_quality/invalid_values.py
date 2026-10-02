"""
DataWise AI — Data Quality: Invalid & Impossible Value Checks
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def detect_invalid_values(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Checks for impossible domain values:
    - Negative values in columns where negative is logically impossible (age, price, tenure, count, revenue, distance)
    - Infinite values (inf, -inf)
    - Suspicious zero concentrations
    """
    issues: List[Dict[str, Any]] = []

    strictly_non_negative_keywords = ["age", "price", "cost", "salary", "income", "tenure", "quantity", "count", "revenue", "sales", "distance"]

    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        col_lower = col.lower()

        # Inf check
        inf_count = int(np.isinf(series).sum())
        if inf_count > 0:
            issues.append({
                "column": col,
                "issue_type": "INFINITE_VALUES",
                "count": inf_count,
                "percentage": round(inf_count / len(series) * 100, 2),
                "severity": "CRITICAL",
                "explanation": f"Column '{col}' contains {inf_count} infinite values.",
            })

        # Negative checks on non-negative candidates
        if any(kw in col_lower for kw in strictly_non_negative_keywords):
            neg_count = int((series < 0).sum())
            if neg_count > 0:
                issues.append({
                    "column": col,
                    "issue_type": "IMPOSSIBLE_NEGATIVE",
                    "count": neg_count,
                    "percentage": round(neg_count / len(series) * 100, 2),
                    "severity": "HIGH",
                    "explanation": f"Column '{col}' is named like a non-negative domain attribute but contains {neg_count} negative entries.",
                })

        # Excessive zeros (>80%)
        zero_count = int((series == 0).sum())
        if len(series) > 0 and (zero_count / len(series)) > 0.80:
            issues.append({
                "column": col,
                "issue_type": "HIGH_ZERO_CONCENTRATION",
                "count": zero_count,
                "percentage": round(zero_count / len(series) * 100, 2),
                "severity": "MEDIUM",
                "explanation": f"Column '{col}' is composed of {round(zero_count / len(series) * 100, 1)}% zeros.",
            })

    return {
        "invalid_issues": issues,
        "issue_count": len(issues),
        "is_clean": len(issues) == 0,
    }
