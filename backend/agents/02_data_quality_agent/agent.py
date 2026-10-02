"""
DataWise AI — Agent 02: Data Quality Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.data_quality import audit_data_quality


class DataQualityAgent:
    """Agent 02: Audits data quality, missing values, duplicates, and impossible values without mutating data."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Data Quality Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Executes quality audit on provided dataset_path or returns initialized state."""
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

                audit_res = audit_data_quality(df)
                score = audit_res["quality_score"]
                missing_cnt = audit_res["missing_analysis"]["missing_columns_count"]
                dup_pct = audit_res["duplicate_analysis"]["duplicate_rows_pct"]

                summary = (
                    f"Data Quality Score: {score}/100. "
                    f"{missing_cnt} columns have missing values. "
                    f"Duplicate rows: {dup_pct}%."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data=audit_res,
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "audit_data_quality", "status": "ready"},
                summary="Data Quality Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Data Quality Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Data Quality Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        """Validate result contract."""
        assert result.agent_name == self.agent_name
        return result
