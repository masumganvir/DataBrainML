"""
DataWise AI — Model Recommendation Agent
Recommends candidate algorithms based on dataset scale, sparsity, and objective.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.ml_recommender import MLRecommender


class ModelRecommendationAgent(BaseAgent):
    """Recommends model candidates and rationale."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Model Recommendation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            target_col = params.get("target_column") or df.columns[-1]
            task_type = params.get("task_type", "classification")

            recommender = MLRecommender(df, target_col=target_col, task_type=task_type)
            recs = recommender.recommend()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Recommended candidate models for {task_type}.",
                data={"recommendations": recs},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
