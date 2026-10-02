"""
Agentic AutoML Intelligence Platform — Retraining Decision Agent
Governs model update actions: CONTINUE, ONLINE_UPDATE, RETRAIN, WAIT, ASK_USER, or ROLLBACK.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from monitoring.retraining_decision import retraining_decision_engine


class RetrainingDecisionAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="RetrainingDecisionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        drift_report = input_data.parameters.get("drift_report", {})
        concept_drift = input_data.parameters.get("concept_drift_report")
        new_samples = input_data.parameters.get("new_samples_count", 0)
        supports_online = input_data.parameters.get("model_supports_online", False)
        human_approval = input_data.parameters.get("human_approval_required", False)

        decision = retraining_decision_engine.evaluate(
            drift_report=drift_report,
            concept_drift_report=concept_drift,
            new_samples_count=new_samples,
            model_supports_online=supports_online,
            human_approval_required=human_approval,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data=decision.model_dump(),
            summary=f"Lifecycle Decision: {decision.action.value}. Justification: {decision.justification}",
            needs_approval=decision.requires_human_approval,
        )
