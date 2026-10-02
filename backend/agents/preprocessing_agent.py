"""
DataWise AI — Preprocessing Agent
Constructs scikit-learn ColumnTransformer ensuring zero data leakage.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.pipeline_builder import PipelineBuilder, build_column_transformer


class PreprocessingAgent(BaseAgent):
    """Builds leak-free ColumnTransformer preprocessing specifications."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Preprocessing Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            target_col = params.get("target_column")
            builder = PipelineBuilder(df=df, target_column=target_col)
            pipeline_def = builder.build()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Constructed sklearn ColumnTransformer definition.",
                data=pipeline_def,
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
