"""
DataWise AI — Dataset Ingestion Agent
Loads data securely from disk or connectors into memory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.storage import storage_manager


class DatasetIngestionAgent(BaseAgent):
    """Responsible for loading datasets into memory without truncation."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Dataset Ingestion Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            path = input_data.dataset_path or input_data.parameters.get("dataset_path")
            if not path or not Path(path).exists():
                return AgentOutput(
                    session_id=self.session_id,
                    agent_name=self.agent_name,
                    status="error",
                    message=f"Dataset path '{path}' does not exist.",
                )

            df = storage_manager.load_dataframe(path)
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Ingested {len(df)} rows × {len(df.columns)} columns.",
                data={"rows": len(df), "columns": list(df.columns), "path": path},
            )
        except Exception as exc:
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="error",
                message=str(exc),
            )
