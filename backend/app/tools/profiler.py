"""
DataWise AI — Dataset Profiler Tool

Performs autonomous, in-depth statistical profiling and schema inference:
  - Per-column descriptive statistics (mean, median, std, IQR, skewness, kurtosis, etc.)
  - Accurate column type categorization:
      * numerical
      * categorical
      * binary
      * datetime
      * free-form text
  - Suspicious column detection:
      * constants (single unique value)
      * near-constants (dominant value > 95%)
      * identifier columns (high unique ratio / ID pattern)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger


from app.state.data_science_state import ColumnInfo


class DatasetProfileResult(dict):
    """Dictionary supporting both item and attribute access for backward compatibility."""
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'DatasetProfileResult' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class DatasetProfiler:

    """Profiles a pandas DataFrame into comprehensive statistical summaries."""

    def __init__(self, df: Any):
        if isinstance(df, (str, Path)):
            from app.tools.storage import load_dataset_file
            self.df = load_dataset_file(str(df))
        else:
            self.df = df
        self.total_rows = len(self.df)
        self.total_cols = len(self.df.columns)


    def profile(self) -> Dict[str, Any]:
        """Runs complete profiling suite and returns structured dictionary."""
        column_profiles: List[ColumnInfo] = []
        numerical_cols: List[str] = []
        categorical_cols: List[str] = []
        binary_cols: List[str] = []
        datetime_cols: List[str] = []
        text_cols: List[str] = []
        identifier_cols: List[str] = []
        constant_cols: List[str] = []
        near_constant_cols: List[str] = []

        for col in self.df.columns:
            series = self.df[col]
            profile_info = self._profile_column(col, series)
            column_profiles.append(profile_info)

            # Categorize
            col_type = profile_info.get("detected_type", "categorical")
            if profile_info.get("is_constant"):
                constant_cols.append(str(col))
            if profile_info.get("is_near_constant"):
                near_constant_cols.append(str(col))
            if profile_info.get("is_identifier"):
                identifier_cols.append(str(col))

            if col_type == "numerical":
                numerical_cols.append(str(col))
            elif col_type == "binary":
                binary_cols.append(str(col))
            elif col_type == "datetime":
                datetime_cols.append(str(col))
            elif col_type == "text":
                text_cols.append(str(col))
            else:
                categorical_cols.append(str(col))

        return DatasetProfileResult({
            "total_rows": self.total_rows,
            "total_columns": self.total_cols,
            "column_profiles": column_profiles,
            "classification": {
                "numerical": numerical_cols,
                "categorical": categorical_cols,
                "binary": binary_cols,
                "datetime": datetime_cols,
                "text": text_cols,
                "identifiers": identifier_cols,
                "constants": constant_cols,
                "near_constants": near_constant_cols,
            },
            "memory_usage_bytes": int(self.df.memory_usage(deep=True).sum()),
            "has_duplicates": bool(self.df.duplicated().any()),
            "duplicate_rows_count": int(self.df.duplicated().sum()),
        })


    def _profile_column(self, col: str, s: pd.Series) -> ColumnInfo:
        """Computes statistical metrics for a single column."""
        total = self.total_rows
        missing = int(s.isnull().sum())
        missing_pct = round((missing / total * 100), 2) if total > 0 else 0.0

        non_null = s.dropna()
        unique_cnt = int(non_null.nunique())
        unique_ratio = round((unique_cnt / total), 4) if total > 0 else 0.0

        is_const = (unique_cnt <= 1 and total > 1)
        is_near_const = False
        if not is_const and unique_cnt > 1 and len(non_null) > 0:
            top_val_freq = non_null.value_counts(normalize=True).iloc[0]
            if top_val_freq >= 0.95:
                is_near_const = True

        # Check if identifier
        is_id = self._is_identifier(col, unique_cnt, unique_ratio, s.dtype)

        # Detect semantic type
        detected_type = self._detect_semantic_type(col, s, non_null, unique_cnt)

        # Base ColumnInfo
        info: ColumnInfo = {
            "name": str(col),
            "dtype": str(s.dtype),
            "unique_count": unique_cnt,
            "unique_ratio": unique_ratio,
            "missing_count": missing,
            "missing_pct": missing_pct,
            "is_identifier": is_id,
            "is_constant": is_const,
            "is_near_constant": is_near_const,
        }
        info["detected_type"] = detected_type  # type: ignore

        # Numerical statistics
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            if len(non_null) > 0:
                vals = non_null.astype(float)
                q1 = float(np.percentile(vals, 25))
                q3 = float(np.percentile(vals, 75))
                mean_val = float(vals.mean())
                std_val = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0

                info["mean"] = round(mean_val, 4)
                info["median"] = round(float(vals.median()), 4)
                info["std"] = round(std_val, 4)
                info["variance"] = round(float(vals.var(ddof=1)), 4) if len(vals) > 1 else 0.0
                info["min"] = round(float(vals.min()), 4)
                info["max"] = round(float(vals.max()), 4)
                info["q1"] = round(q1, 4)
                info["q3"] = round(q3, 4)
                info["iqr"] = round(q3 - q1, 4)
                info["zero_count"] = int((vals == 0).sum())
                info["negative_count"] = int((vals < 0).sum())

                # Skewness and kurtosis
                if len(vals) >= 3 and std_val > 0:
                    info["skewness"] = round(float(vals.skew()), 4)
                    info["kurtosis"] = round(float(vals.kurtosis()), 4)
                else:
                    info["skewness"] = 0.0
                    info["kurtosis"] = 0.0

        # Mode
        if len(non_null) > 0:
            mode_series = s.mode()
            if not mode_series.empty:
                val = mode_series.iloc[0]
                info["mode"] = str(val) if not isinstance(val, (int, float, bool)) else val

        return info

    def _is_identifier(self, col_name: str, unique_cnt: int, unique_ratio: float, dtype: Any) -> bool:
        """Identifies columns likely to be surrogate IDs or keys."""
        col_lower = str(col_name).lower()
        id_patterns = [r"_id$", r"^id$", r"uuid", r"guid", r"_key$", r"^key$", r"customer_id", r"user_id", r"transaction_id"]

        matches_name = any(re.search(pat, col_lower) for pat in id_patterns)
        if matches_name and (unique_ratio > 0.6 or unique_cnt > 50):
            return True

        # Purely unique string or integer in large dataset
        if unique_ratio > 0.98 and self.total_rows >= 50:
            return True

        return False

    def _detect_semantic_type(self, col: str, s: pd.Series, non_null: pd.Series, unique_cnt: int) -> str:
        """Determines semantic type: numerical, binary, datetime, text, or categorical."""
        if pd.api.types.is_bool_dtype(s):
            return "binary"

        if unique_cnt == 2:
            return "binary"

        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(s):
            return "datetime"

        if pd.api.types.is_string_dtype(s) or s.dtype == object or str(s.dtype).startswith("str"):
            # Attempt datetime parse on small sample
            if len(non_null) > 0:
                sample = non_null.head(20).astype(str)
                try:
                    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
                    if parsed.notnull().mean() >= 0.8:
                        return "datetime"
                except Exception:
                    pass

            # Free-form text vs categorical
            if len(non_null) > 0:
                avg_word_count = non_null.astype(str).str.split().str.len().mean()
                avg_char_length = non_null.astype(str).str.len().mean()
                if avg_word_count > 3 or avg_char_length > 60:
                    return "text"

            return "categorical"

        if pd.api.types.is_numeric_dtype(s):
            return "numerical"

        return "categorical"


def profile_dataframe(df_or_path: Any) -> Dict[str, Any]:
    """Helper entry point for profiling a pandas DataFrame or file path."""
    profiler = DatasetProfiler(df_or_path)
    return profiler.profile()


profile_dataset = profile_dataframe
DatasetProfile = DatasetProfiler


