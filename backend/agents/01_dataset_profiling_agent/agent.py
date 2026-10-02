"""
DataWise AI — Agent 01: Dataset Profiling Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.profiling import profile_dataset


class DatasetProfilerAgent:
    """Agent 01: Understands dataset shape, schema, column types, and statistics without mutating data."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Dataset Profiling Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Executes profiling on provided dataset_path or returns initialized state."""
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                path = input_data.dataset_path
                ext = Path(path).suffix.lower()
                if ext in (".xlsx", ".xls"):
                    df = pd.read_excel(path)
                elif ext == ".json":
                    df = pd.read_json(path)
                else:
                    df = pd.read_csv(path, low_memory=False)

                profile_res = profile_dataset(df)
                summary = (
                    f"Dataset profiled: {profile_res['summary']['total_rows']} rows, "
                    f"{profile_res['summary']['total_columns']} columns "
                    f"({profile_res['summary']['numeric_count']} numeric, "
                    f"{profile_res['summary']['categorical_count']} categorical)."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data=profile_res,
                    summary=summary,
                ))

            # Default / initialized return if no dataset path provided
            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "profile_dataset", "status": "ready"},
                summary="Dataset Profiling Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Dataset Profiling Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Dataset Profiling Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        """Validate output contract."""
        assert result.agent_name == self.agent_name
        return result
