"""
DataWise AI — Transformation Agent
Analyzes feature skewness and determines power / log / Yeo-Johnson transformations.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.transformation import FeatureTransformer


class TransformationAgent(BaseAgent):
    """Recommends and applies distribution transformations."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Transformation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            transformer = FeatureTransformer(df)
            plan = transformer.generate_plan()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Feature transformation plan generated.",
                data={"transformation_plan": plan},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
