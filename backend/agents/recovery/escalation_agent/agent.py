"""
Escalation Agent
Intervenes when human approval is required for destructive changes or security halts.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.escalation_manager import EscalationManager


class EscalationAgent(BaseAgent):
    """Enforces human-in-the-loop review for destructive actions and security incidents."""

    def __init__(self, session_id: str = "", agent_name: str = "EscalationAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)
        self.escalation_manager = EscalationManager()

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        workflow_id = input_data.session_id or params.get("workflow_id", "default_workflow")
        error_id = params.get("error_id", "ERR-UNKNOWN")
        reason = params.get("reason", "Destructive or security-sensitive action requires authorization.")
        action_type = params.get("action_type", "general_approval")

        req = self.escalation_manager.create_escalation(
            workflow_id=workflow_id,
            error_id=error_id,
            reason=reason,
            action_type=action_type,
            approval_options=["Approve", "Reject", "Abort"],
            context=params,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="needs_approval",
            needs_approval=True,
            approval_context={
                "escalation_id": req.escalation_id,
                "reason": req.reason,
                "action_type": req.action_type,
                "options": req.approval_options,
            },
            summary=f"Escalated to human operator: {req.reason}",
            data=req.model_dump(),
        )
