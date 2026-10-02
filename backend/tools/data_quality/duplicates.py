"""
DataWise AI — Data Quality: Duplicate Detection
"""

from typing import Any, Dict, List
import pandas as pd


def detect_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    """Detects exact duplicate rows and identical/redundant columns."""
    n_rows = len(df)
    duplicate_rows_count = int(df.duplicated().sum())
    duplicate_rows_pct = round((duplicate_rows_count / max(n_rows, 1)) * 100, 2)

    # Detect duplicate columns
    duplicate_columns: List[List[str]] = []
    cols = list(df.columns)
    seen_identical = set()

    for i in range(len(cols)):
        col_a = cols[i]
        if col_a in seen_identical:
            continue
        group = [col_a]
        for j in range(i + 1, len(cols)):
            col_b = cols[j]
            if col_b in seen_identical:
                continue
            if df[col_a].equals(df[col_b]):
                group.append(col_b)
                seen_identical.add(col_b)
        if len(group) > 1:
            duplicate_columns.append(group)

    return {
        "duplicate_rows_count": duplicate_rows_count,
        "duplicate_rows_pct": duplicate_rows_pct,
        "has_duplicate_rows": duplicate_rows_count > 0,
        "duplicate_column_groups": duplicate_columns,
        "has_duplicate_columns": len(duplicate_columns) > 0,
    }
