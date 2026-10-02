"""
DataWise AI — Feature Selection Agent
Selects non-redundant, predictive features via Mutual Information, ANOVA, and VarianceThreshold.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.feature_selection import FeatureSelector


class FeatureSelectionAgent(BaseAgent):
    """Selects optimal predictive feature subsets."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Feature Selection Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            target_col = params.get("target_column") or df.columns[-1]
            fs = FeatureSelector(df, target_column=target_col)
            selected = fs.select_features()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Selected features based on relevance scores.",
                data={"selected_features": selected},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
