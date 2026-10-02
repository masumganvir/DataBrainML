"""
DataWise AI — Agent 09: Data Leakage Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.leakage import audit_dataset_leakage


class DataLeakageAgent:
    """Agent 09: Strict data leakage auditor and pipeline gatekeeper."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Data Leakage Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
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

                target = input_data.parameters.get("target_column")
                time_col = input_data.parameters.get("time_column")

                if not target or target not in df.columns:
                    target = df.columns[-1]

                leakage_res = audit_dataset_leakage(df, target_column=target, time_column=time_col)
                blocked = leakage_res.get("should_block_pipeline", False)
                leaked_feats = leakage_res.get("leaked_features", [])

                if blocked:
                    summary = (
                        f"CRITICAL WARNING: Data Leakage detected in {len(leaked_feats)} feature(s): {leaked_feats}. "
                        "Pipeline progression is blocked until resolved."
                    )
                else:
                    summary = "Leakage Audit Passed: No target duplication or critical proxy leakage detected."

                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="warning" if blocked else "success",
                    data=leakage_res,
                    summary=summary,
                    warnings=[f"Leaked feature: {f}" for f in leaked_feats],
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "audit_dataset_leakage", "status": "ready"},
                summary="Data Leakage Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Data Leakage Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Data Leakage Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
