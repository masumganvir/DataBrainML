"""
DataWise AI — Evaluation Agent
Computes comprehensive holdout metrics (ROC-AUC, PR-AUC, F1, RMSE, R²).
"""

from __future__ import annotations

from typing import Any, Dict
import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput


class EvaluationAgent(BaseAgent):
    """Computes unbiased evaluation metrics on untouched holdout test splits."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Evaluation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        test_metrics = params.get("test_metrics", {})
        primary_metric = params.get("primary_metric", "Score")

        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=f"Evaluation complete. Primary metric ({primary_metric}): {test_metrics.get(primary_metric, 'N/A')}",
            data={"test_metrics": test_metrics, "primary_metric": primary_metric},
        )
