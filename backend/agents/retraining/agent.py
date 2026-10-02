"""
DataWise AI — Retraining Agent
Governs champion-challenger retraining triggered by data drift.
Evaluates challenger against production baseline.
CRITICAL: Never silently replaces production models without verification and approval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class RetrainingAgent(BaseAgent):
    """Automated Retraining & Challenger Validation Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Retraining Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        prod_score = float(params.get("production_score", 0.82))
        challenger_score = float(params.get("challenger_score", 0.87))
        drift_reason = params.get("trigger_reason", "Statistical covariate drift exceeding PSI threshold 0.25")

        delta = round(challenger_score - prod_score, 4)
        is_improved = delta > 0.01

        if is_improved:
            status = "needs_approval"
            action = "PROPOSE_PROMOTION"
            summary = (
                f"Retraining successful: Challenger model ({challenger_score:.4f}) outperforms "
                f"Production ({prod_score:.4f}) by +{delta:.2%}. Promotion requires human approval."
            )
        else:
            status = "warning"
            action = "KEEP_PRODUCTION"
            summary = (
                f"Retraining completed but challenger ({challenger_score:.4f}) failed to demonstrate "
                f"significant improvement over Production ({prod_score:.4f}). Retaining current production version."
            )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status=status,
            data={
                "trigger_reason": drift_reason,
                "production_score": prod_score,
                "challenger_score": challenger_score,
                "score_delta": delta,
                "is_improved": is_improved,
                "recommended_action": action,
            },
            needs_approval=is_improved,
            approval_context={
                "action": "Promote challenger model to production",
                "delta": delta,
                "prod_score": prod_score,
                "challenger_score": challenger_score,
            } if is_improved else None,
            summary=summary,
        )
