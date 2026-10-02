"""
Validation Agent
Independently verifies recovered data schemas, preprocessing pipelines,
models, and deployment states before permitting resumption.
"""

from __future__ import annotations

import pandas as pd
from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.validation_manager import ValidationManager


class ValidationAgent(BaseAgent):
    """Executes validation gates to guarantee recovered artifacts are fully functional."""

    def __init__(self, session_id: str = "", agent_name: str = "ValidationAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        stage = params.get("stage", "data_validation")
        target_obj = params.get("target_object")

        if stage == "data_validation" or isinstance(target_obj, pd.DataFrame):
            report = ValidationManager.validate_data_schema(target_obj)
        elif stage == "preprocessing_validation":
            sample_df = params.get("sample_df", pd.DataFrame({"a": [1.0, 2.0]}))
            report = ValidationManager.validate_preprocessing_pipeline(target_obj, sample_df)
        elif stage == "model_validation":
            sample_x = params.get("sample_features", [[1.0, 2.0], [3.0, 4.0]])
            report = ValidationManager.validate_model_inference(target_obj, sample_x)
        else:
            report = ValidationManager.validate_data_schema(target_obj if isinstance(target_obj, pd.DataFrame) else None)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if report.is_valid else "error",
            summary=f"Validation result: {'PASSED' if report.is_valid else 'FAILED'} ({report.validation_message})",
            data=report.model_dump(),
        )
