"""
DataWise AI — Overfitting / Underfitting Agent
Analyzes the generalization gap between train and test/cross-validation scores.
"""

from __future__ import annotations

from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput


class OverfittingAgent(BaseAgent):
    """Analyzes model bias-variance tradeoff and generalization gap."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Overfitting Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        train_score = params.get("train_score", 0.0)
        test_score = params.get("test_score", 0.0)

        gap = abs(train_score - test_score)
        if gap > 0.15:
            health = "Warning: Moderate Overfitting"
            reason = f"Train score ({train_score:.3f}) exceeds test score ({test_score:.3f}) by {gap*100:.1f}%."
            mitigation = "Increase regularization (min_samples_split, alpha) or reduce tree depth."
        elif train_score < 0.55 and test_score < 0.55:
            health = "Warning: Underfitting"
            reason = f"Both train ({train_score:.3f}) and test ({test_score:.3f}) scores are low."
            mitigation = "Increase model capacity, engineer non-linear interaction terms, or collect more features."
        else:
            health = "Healthy"
            reason = f"Train score ({train_score:.3f}) vs Test score ({test_score:.3f}) exhibits low variance gap ({gap*100:.1f}%)."
            mitigation = "None required. Generalization boundary is well-regularized."

        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=f"Generalization check: {health}",
            data={
                "health": health,
                "reason": reason,
                "mitigation": mitigation,
                "train_score": train_score,
                "test_score": test_score,
                "gap": round(gap, 4),
            },
        )
