"""
DataWise AI — Outlier Analysis Agent
Evaluates extreme observations (IQR, Z-Score, Isolation Forest) without assuming outliers = bad data.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.outlier_decision_engine import OutlierDecisionEngine


class OutlierAnalysisAgent(BaseAgent):
    """Analyzes outliers intelligently and generates treatment recommendations."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Outlier Analysis Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            target_col = params.get("target_column")
            engine = OutlierDecisionEngine(df, target_col=target_col)
            decisions = engine.generate_decisions()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Evaluated outliers across numerical features.",
                data={"decisions": decisions},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
