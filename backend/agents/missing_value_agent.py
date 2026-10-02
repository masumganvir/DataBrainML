"""
DataWise AI — Missing Value Agent
Audits missingness patterns and recommends adaptive imputation strategies.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.missing_value_engine import MissingValueEngine


class MissingValueAgent(BaseAgent):
    """Detects and plans imputation for missing data."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Missing Value Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            engine = MissingValueEngine(df)
            plan = engine.generate_imputation_plan()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Generated imputation plan for {len(plan)} columns.",
                data={"imputation_plan": plan},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
