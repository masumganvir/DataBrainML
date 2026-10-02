"""
DataWise AI — Intake Agent
Specialized agent for dataset ingestion, schema validation, and storage auditing.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState


class IntakeAgent(BaseAgent):
    """Handles raw dataset ingestion, format verification, and initial metadata extraction."""

    def __init__(self) -> None:
        super().__init__(
            name="IntakeAgent",
            role="Data Ingestion & Schema Verification Specialist",
            description="Validates uploaded datasets, examines file integrity, and extracts basic dimensions.",
            system_prompt=(
                "You specialize in raw dataset ingestion and validation. "
                "Assess dataset dimensions, column counts, missing columns, and file format risks. "
                "Guide the user on proper data formats (CSV, XLSX, Parquet, JSON)."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Ingesting dataset for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            err = {"stage": "INGEST", "error": "Unable to read dataset from specified path."}
            return {**state, "errors": [*state.get("errors", []), err]}

        row_count, col_count = df.shape
        file_size = 0
        path = state.get("dataset_path_analysis") or state.get("dataset_path_original")
        if path and os.path.exists(path):
            file_size = os.path.getsize(path)

        logger.info(f"[{self.name}] Successfully ingested {row_count} rows x {col_count} columns ({file_size} bytes)")

        return {
            **state,
            "row_count_original": row_count,
            "column_count_original": col_count,
            "row_count_current": row_count,
            "column_count_current": col_count,
            "current_stage": "PROFILE",
            "completed_stages": [*state.get("completed_stages", []), "INGEST"],
        }
