"""
DataWise AI — Profiling: Schema Extraction
"""

from typing import Any, Dict, List
import pandas as pd


def extract_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Classifies column types into numerical, categorical, binary, datetime, text, and identifier."""
    columns_info = {}
    numerical_cols: List[str] = []
    categorical_cols: List[str] = []
    binary_cols: List[str] = []
    datetime_cols: List[str] = []
    text_cols: List[str] = []
    identifier_cols: List[str] = []

    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)
        unique_cnt = series.nunique(dropna=True)
        unique_ratio = unique_cnt / max(n_rows, 1)

        is_binary = unique_cnt == 2
        is_id = False

        if pd.api.types.is_numeric_dtype(series):
            if is_binary and not pd.api.types.is_float_dtype(series):
                binary_cols.append(col)
                col_type = "binary"
            else:
                numerical_cols.append(col)
                col_type = "numerical"
        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
            col_type = "datetime"
        else:
            # Try parsing datetime if object
            sample = series.dropna().head(20)
            is_dt = False
            if len(sample) > 0 and sample.astype(str).str.len().mean() > 6:
                try:
                    pd.to_datetime(sample, format="mixed")
                    is_dt = True
                except Exception:
                    pass

            if is_dt:
                datetime_cols.append(col)
                col_type = "datetime"
            elif is_binary:
                binary_cols.append(col)
                col_type = "binary"
            elif unique_ratio > 0.85 and n_rows > 30 and series.astype(str).str.len().mean() < 30:
                identifier_cols.append(col)
                col_type = "identifier"
                is_id = True
            elif series.astype(str).str.len().mean() > 50:
                text_cols.append(col)
                col_type = "text"
            else:
                categorical_cols.append(col)
                col_type = "categorical"

        columns_info[col] = {
            "name": col,
            "dtype": dtype_str,
            "inferred_type": col_type,
            "unique_count": unique_cnt,
            "unique_ratio": round(unique_ratio, 4),
            "is_identifier": is_id,
            "is_binary": is_binary,
        }

    return {
        "columns": columns_info,
        "numerical_columns": numerical_cols,
        "categorical_columns": categorical_cols,
        "binary_columns": binary_cols,
        "datetime_columns": datetime_cols,
        "text_columns": text_cols,
        "identifier_columns": identifier_cols,
        "total_columns": len(df.columns),
        "total_rows": n_rows,
    }
