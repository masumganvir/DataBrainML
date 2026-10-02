"""
DataWise AI — Agent 04: Outlier Intelligence Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.outliers import analyze_all_outliers

OUTLIER_MAX_ITERATIONS = 3


class OutlierDecisionAgent:
    """Agent 04: Context-aware outlier analyzer preserving rare signals."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Outlier Intelligence Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            iteration = input_data.parameters.get("loop_iteration", 1)
            if iteration > OUTLIER_MAX_ITERATIONS:
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={"loop_halted": True, "reason": f"OUTLIER_MAX_ITERATIONS ({OUTLIER_MAX_ITERATIONS}) reached."},
                    summary="Outlier analysis iteration budget reached.",
                ))

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
                outliers_res = analyze_all_outliers(df, target_column=target)
                outliers_res["loop_iteration"] = iteration

                out_count = outliers_res["features_with_outliers_count"]
                summary = (
                    f"Outlier Intelligence evaluated {len(df.columns)} columns (iteration {iteration}/{OUTLIER_MAX_ITERATIONS}). "
                    f"{out_count} features contain statistical outliers. "
                    "Context-aware recommendations formulated (zero silent deletions)."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data=outliers_res,
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "analyze_all_outliers", "status": "ready"},
                summary="Outlier Intelligence Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Outlier Intelligence Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Outlier Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
