"""
DataWise AI — Profiling Agent
Specialized agent for column profiling, statistical summary, and type classification.
"""

from __future__ import annotations

from typing import List, Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.profiler import profile_dataframe


class ProfilingAgent(BaseAgent):
    """Profiles columns, computes statistical summaries, and classifies feature data types."""

    def __init__(self) -> None:
        super().__init__(
            name="ProfilingAgent",
            role="Statistical Profiler & Data Type Analyst",
            description="Computes descriptive statistics, unique values, cardinality, and classifies numerical vs categorical columns.",
            system_prompt=(
                "You are an expert in statistical data profiling and type classification. "
                "Explain column distributions, variance, min/max values, skewness, and potential ID columns. "
                "Highlight constant or high-cardinality features that might need special treatment."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Running profiling for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "PROFILE", "error": "Dataset not found for profiling."}],
            }

        try:
            result = profile_dataframe(df)
            classification = result.get("classification", {})
            profiles = result.get("column_profiles") or result.get("columns", [])
            return {
                **state,
                "column_profiles": profiles,
                "numerical_columns": classification.get("numerical", []),
                "categorical_columns": classification.get("categorical", []),
                "binary_columns": classification.get("binary", []),
                "datetime_columns": classification.get("datetime", []),
                "text_columns": classification.get("text", []),
                "identifier_columns": classification.get("identifiers", []),
                "constant_columns": classification.get("constants", []),
                "current_stage": "QUALITY",
                "completed_stages": [*state.get("completed_stages", []), "PROFILE"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Profiling failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "PROFILE", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        profiles = state.get("column_profiles", [])
        num_cols = state.get("numerical_columns", [])
        cat_cols = state.get("categorical_columns", [])
        id_cols = state.get("identifier_columns", [])
        const_cols = state.get("constant_columns", [])
        return (
            f"Dataset Columns: {len(profiles)}\n"
            f"Numerical: {num_cols}\n"
            f"Categorical: {cat_cols}\n"
            f"Identifier columns: {id_cols}\n"
            f"Constant columns: {const_cols}"
        )
