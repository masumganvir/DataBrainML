"""
DataWise AI — Scaling Agent
Selects appropriate scaling techniques (StandardScaler, RobustScaler, MinMaxScaler).
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.scaling import ScalingRecommender


class ScalingAgent(BaseAgent):
    """Recommends and applies feature scaling strategies."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Scaling Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            recommender = ScalingRecommender(df)
            plan = recommender.recommend_all()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Scaling strategy selected for numerical features.",
                data={"scaling_plan": plan},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
