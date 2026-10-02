"""
DataWise AI — Feature Engineering Agent
Engineers interactions, ratios, date features, and domain transformations.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.feature_engineering import FeatureEngineer


class FeatureEngineeringAgent(BaseAgent):
    """Engineers informative new features with complete lineage."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Feature Engineering Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            fe = FeatureEngineer(df, target_column=params.get("target_column"))
            res = fe.engineer_features()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Engineered features successfully.",
                data=res,
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
