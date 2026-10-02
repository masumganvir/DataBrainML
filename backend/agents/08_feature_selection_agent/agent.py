"""
DataWise AI — Agent 08: Feature Selection Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.feature_selection import run_feature_selection_suite, FEATURE_SELECTION_MAX_ITERATIONS


class FeatureAgent:
    """Agent 08: Multi-criterion feature selection bounded by loop constraints."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Feature Selection Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            iteration = input_data.parameters.get("loop_iteration", 1)
            if iteration > FEATURE_SELECTION_MAX_ITERATIONS:
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={"loop_halted": True, "reason": f"FEATURE_SELECTION_MAX_ITERATIONS ({FEATURE_SELECTION_MAX_ITERATIONS}) reached."},
                    summary="Feature selection iteration budget reached.",
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
                task = input_data.parameters.get("task_type", "classification")

                if not target or target not in df.columns:
                    target = df.columns[-1]

                res = run_feature_selection_suite(df, target_column=target, task_type=task)
                res["loop_iteration"] = iteration

                summary = (
                    f"Feature Selection (iter {iteration}/{FEATURE_SELECTION_MAX_ITERATIONS}): "
                    f"Selected {res['selected_feature_count']} of {res['original_feature_count']} features "
                    f"(pruned collinear & zero-variance noise)."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data=res,
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "run_feature_selection_suite", "status": "ready"},
                summary="Feature Selection Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Feature Selection Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Feature Selection Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
