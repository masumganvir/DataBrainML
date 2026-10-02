"""
DataWise AI — Encoding Agent
Determines and executes safe categorical encoding strategies.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.encoding import CategoricalEncoder


class EncodingAgent(BaseAgent):
    """Categorical encoding planner and executor."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Encoding Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            encoder = CategoricalEncoder(df, target_column=params.get("target_column"))
            plan = encoder.generate_plan()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Categorical encoding planned for {len(plan)} columns.",
                data={"encoding_plan": plan},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
