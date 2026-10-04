"""
DataWise AI — Dataset Profiler Agent
Section 6 Specification:
Determines rows, columns, data types, unique values, missing values, duplicate rows,
constant columns, near-constant columns, numeric columns, categorical columns,
datetime columns, text columns, boolean columns, high-cardinality columns, potential ID columns.
Produces dataset_profile.json and updates EDAState.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class DatasetProfilerAgent:
    """Performs deep, leak-free statistical profiling of tabular data."""

    def __init__(self, name: str = "DatasetProfilerAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        """Executes profiling on dataframe or dataset_path in state."""
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path or not Path(dataset_path).exists():
                    raise FileNotFoundError(f"Dataset path not found: {dataset_path}")
                df = pd.read_csv(dataset_path)

            n_rows, n_cols = df.shape
            state["row_count"] = n_rows
            state["column_count"] = n_cols

            # Detect ID columns
            id_pattern = re.compile(r"(^id$|_id$|^id_|uuid|guid|key|index|row_num|record)", re.IGNORECASE)
            id_cols = [
                c for c in df.columns
                if (id_pattern.search(c) and df[c].nunique() > min(50, max(20, n_rows * 0.2)))
                or (n_rows > 500 and df[c].nunique() > n_rows * 0.7)
            ]

            # Categorize columns
            numeric_cols = []
            categorical_cols = []
            datetime_cols = []
            text_cols = []
            boolean_cols = []
            constant_cols = []
            near_constant_cols = []
            high_cardinality_cols = []

            column_details: Dict[str, Any] = {}

            for col in df.columns:
                series = df[col]
                n_unique = series.nunique(dropna=True)
                null_count = int(series.isnull().sum())
                null_pct = round((null_count / max(1, n_rows)) * 100, 2)
                dtype_str = str(series.dtype)

                # Check constant / near constant
                if n_unique <= 1:
                    constant_cols.append(col)
                elif n_rows > 20 and (series.value_counts(normalize=True, dropna=False).iloc[0] > 0.95):
                    near_constant_cols.append(col)

                # Check boolean
                if n_unique == 2 and set(series.dropna().unique()).issubset({0, 1, True, False, "0", "1", "true", "false", "True", "False"}):
                    boolean_cols.append(col)

                # Check datetime
                is_dt = False
                if pd.api.types.is_datetime64_any_dtype(series):
                    is_dt = True
                elif dtype_str == "object" and not series.dropna().empty:
                    sample = series.dropna().head(10).astype(str)
                    if any(c in col.lower() for c in ["date", "time", "timestamp", "year", "created", "updated"]):
                        try:
                            pd.to_datetime(sample, errors="raise")
                            is_dt = True
                        except Exception:
                            is_dt = False

                if is_dt:
                    datetime_cols.append(col)
                    col_type = "datetime"
                elif pd.api.types.is_numeric_dtype(series) and col not in boolean_cols:
                    numeric_cols.append(col)
                    col_type = "numeric"
                elif col in boolean_cols:
                    categorical_cols.append(col)
                    col_type = "boolean"
                else:
                    # String / Categorical / Text
                    avg_len = series.dropna().astype(str).str.len().mean() if not series.dropna().empty else 0
                    if avg_len > 60:
                        text_cols.append(col)
                        col_type = "text"
                    else:
                        categorical_cols.append(col)
                        col_type = "categorical"
                        if n_unique > 50 and n_unique > n_rows * 0.05:
                            high_cardinality_cols.append(col)

                col_stat: Dict[str, Any] = {
                    "dtype": dtype_str,
                    "inferred_type": col_type,
                    "unique_count": n_unique,
                    "missing_count": null_count,
                    "missing_percentage": null_pct,
                    "is_id": col in id_cols,
                }

                if col_type == "numeric":
                    clean = series.dropna()
                    if not clean.empty:
                        col_stat["mean"] = round(float(clean.mean()), 4)
                        col_stat["std"] = round(float(clean.std()), 4) if len(clean) > 1 else 0.0
                        col_stat["min"] = round(float(clean.min()), 4)
                        col_stat["max"] = round(float(clean.max()), 4)
                        col_stat["median"] = round(float(clean.median()), 4)
                        col_stat["skew"] = round(float(clean.skew()), 4) if len(clean) > 2 else 0.0
                elif col_type in ("categorical", "boolean"):
                    top_vals = series.value_counts(dropna=True).head(5).to_dict()
                    col_stat["top_categories"] = {str(k): int(v) for k, v in top_vals.items()}

                column_details[col] = col_stat

            duplicates_count = int(df.duplicated().sum())
            duplicate_pct = round((duplicates_count / max(1, n_rows)) * 100, 2)

            profile_payload = {
                "dataset_id": state.get("dataset_id"),
                "rows": n_rows,
                "columns": n_cols,
                "duplicates_count": duplicates_count,
                "duplicates_percentage": duplicate_pct,
                "constant_columns": constant_cols,
                "near_constant_columns": near_constant_cols,
                "id_columns": id_cols,
                "high_cardinality_columns": high_cardinality_cols,
                "column_counts": {
                    "numeric": len(numeric_cols),
                    "categorical": len(categorical_cols),
                    "datetime": len(datetime_cols),
                    "text": len(text_cols),
                    "boolean": len(boolean_cols),
                },
                "columns": column_details,
            }

            state["dataset_profile"] = profile_payload
            state["numeric_columns"] = numeric_cols
            state["categorical_columns"] = categorical_cols
            state["datetime_columns"] = datetime_cols
            state["text_columns"] = text_cols
            state["column_types"] = {c: column_details[c]["inferred_type"] for c in df.columns}
            state.setdefault("completed_steps", []).append("dataset_profiling")

            # Save dataset_profile.json
            output_dir = Path(state.get("output_dir", f"artifacts/{state.get('run_id', 'run_001')}/visualizations")).parent
            profile_path = output_dir / "dataset_profile.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(profile_payload, f, indent=2)
            state.setdefault("artifacts", {})["dataset_profile"] = str(profile_path)

            logger.info(f"[{self.name}] Profiled {n_rows} rows × {n_cols} cols ({len(numeric_cols)} num, {len(categorical_cols)} cat).")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in dataset profiling: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})
            state.setdefault("warnings", []).append(f"Profiling completed with fallback: {exc}")

        return state
