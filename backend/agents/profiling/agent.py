"""
DataWise AI — Profiling Agent
Computes deep statistical profiles for numerical, categorical, datetime, text,
identifier, and constant columns. Python computes; LLM explains.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class ProfilingAgent(BaseAgent):
    """Profiling Agent: Produces detailed machine-readable dataset statistics."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Profiling Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Profiling failed: unable to load dataset.",
                errors=["Dataset path invalid or empty"],
            )

        n_rows, n_cols = df.shape
        numerical_cols: List[str] = []
        categorical_cols: List[str] = []
        datetime_cols: List[str] = []
        text_cols: List[str] = []
        identifier_cols: List[str] = []
        constant_cols: List[str] = []
        near_constant_cols: List[str] = []
        column_profiles: List[Dict[str, Any]] = []

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_pct = round((missing_count / n_rows) * 100, 2)
            non_null = series.dropna()
            unique_count = int(non_null.nunique())
            unique_ratio = round(unique_count / max(len(non_null), 1), 4)

            # Identifier detection: high uniqueness (>95%) and string/int sequence
            is_id = False
            col_lower = col.lower()
            if (unique_ratio > 0.95 and n_rows > 30) or any(k in col_lower for k in ["id", "uuid", "guid", "key", "token"]):
                is_id = True
                identifier_cols.append(col)

            # Constant / near-constant
            is_constant = unique_count <= 1
            if is_constant:
                constant_cols.append(col)

            is_near_constant = False
            if not is_constant and len(non_null) > 0:
                top_val_freq = non_null.value_counts(normalize=True).iloc[0]
                if top_val_freq >= 0.95:
                    is_near_constant = True
                    near_constant_cols.append(col)

            # Type classification
            col_info: Dict[str, Any] = {
                "name": col,
                "dtype": str(series.dtype),
                "unique_count": unique_count,
                "unique_ratio": unique_ratio,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "is_identifier": is_id,
                "is_constant": is_constant,
                "is_near_constant": is_near_constant,
            }

            if pd.api.types.is_numeric_dtype(series) and not is_id and unique_count > 2:
                numerical_cols.append(col)
                vals = pd.to_numeric(non_null, errors="coerce").dropna()
                if len(vals) > 0:
                    q1 = float(vals.quantile(0.25))
                    q3 = float(vals.quantile(0.75))
                    col_info.update({
                        "type_category": "numerical",
                        "mean": round(float(vals.mean()), 4),
                        "std": round(float(vals.std()), 4) if len(vals) > 1 else 0.0,
                        "min": round(float(vals.min()), 4),
                        "max": round(float(vals.max()), 4),
                        "median": round(float(vals.median()), 4),
                        "q1": round(q1, 4),
                        "q3": round(q3, 4),
                        "iqr": round(q3 - q1, 4),
                        "skewness": round(float(stats.skew(vals)), 4) if len(vals) > 2 else 0.0,
                        "kurtosis": round(float(stats.kurtosis(vals)), 4) if len(vals) > 3 else 0.0,
                        "zero_count": int((vals == 0).sum()),
                    })
            elif pd.api.types.is_datetime64_any_dtype(series) or "date" in col_lower or "time" in col_lower:
                # Test if datetime convertible
                try:
                    dt_series = pd.to_datetime(non_null.head(100))
                    datetime_cols.append(col)
                    col_info["type_category"] = "datetime"
                except Exception:
                    categorical_cols.append(col)
                    col_info["type_category"] = "categorical"
            else:
                # Text vs Categorical
                if unique_count > 100 and unique_ratio > 0.3:
                    text_cols.append(col)
                    col_info["type_category"] = "text"
                else:
                    categorical_cols.append(col)
                    col_info["type_category"] = "categorical"
                    top_cats = non_null.value_counts().head(5).to_dict()
                    col_info["top_categories"] = {str(k): int(v) for k, v in top_cats.items()}

            column_profiles.append(col_info)

        # Correlation matrix for numerical
        correlations = {}
        if len(numerical_cols) >= 2:
            num_df = df[numerical_cols].dropna()
            if len(num_df) > 5:
                corr_matrix = num_df.corr().round(3).to_dict()
                correlations = corr_matrix

        profile_summary = {
            "total_rows": n_rows,
            "total_columns": n_cols,
            "numerical_columns": numerical_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "text_columns": text_cols,
            "identifier_columns": identifier_cols,
            "constant_columns": constant_cols,
            "near_constant_columns": near_constant_cols,
            "column_profiles": column_profiles,
            "correlations": correlations,
        }

        summary = (
            f"Profiled {n_rows:,} rows and {n_cols} columns: "
            f"{len(numerical_cols)} numerical, {len(categorical_cols)} categorical, "
            f"{len(datetime_cols)} datetime, {len(identifier_cols)} identifier(s), "
            f"{len(constant_cols)} constant column(s)."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"profile": profile_summary},
            summary=summary,
        )
