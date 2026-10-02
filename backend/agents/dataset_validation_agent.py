"""
DataWise AI — Dataset Validation Agent
Validates file integrity, encoding, column headers, and structural validity.
"""

from __future__ import annotations

import pandas as pd
from loguru import logger
from agents.base import BaseAgent, AgentInput, AgentOutput


class DatasetValidationAgent(BaseAgent):
    """Validates dataset health and schema readiness."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Dataset Validation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        df = params.get("df")
        if df is None and input_data.dataset_path:
            try:
                df = pd.read_csv(input_data.dataset_path)
            except Exception as e:
                return AgentOutput(
                    session_id=self.session_id,
                    agent_name=self.agent_name,
                    status="error",
                    message=f"Validation failed: {e}",
                )

        if df is None or df.empty:
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="error",
                message="Dataset is empty or invalid.",
            )

        empty_cols = [c for c in df.columns if df[c].isnull().all()]
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=f"Dataset validated: {len(df)} rows, {len(df.columns)} columns.",
            data={"rows": len(df), "cols": len(df.columns), "all_empty_columns": empty_cols},
        )
