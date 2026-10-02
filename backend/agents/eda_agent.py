"""
DataWise AI — EDA Agent
Performs in-depth exploratory data analysis and correlation detection.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.correlations import CorrelationAnalyzer
from app.tools.distributions import DistributionAnalyzer


class EDAAgent(BaseAgent):
    """Exploratory data analysis agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "EDA Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            corr = CorrelationAnalyzer(df).analyze()
            dist = DistributionAnalyzer(df).analyze()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Completed correlation and distribution exploration.",
                data={"correlations": corr, "distributions": dist},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
