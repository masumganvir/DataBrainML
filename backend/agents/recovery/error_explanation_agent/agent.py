"""
Error Explanation Agent
Generates clear, transparent, actionable user-facing failure explanations
without exposing sensitive implementation details or stack traces.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.safe_error_formatter import SafeErrorFormatter


class ErrorExplanationAgent(BaseAgent):
    """Produces actionable, user-safe error summaries following the 5-point contract."""

    def __init__(self, session_id: str = "", agent_name: str = "ErrorExplanationAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        error_id = params.get("error_id", "ERR-GENERIC")
        stage = params.get("stage", "Execution")
        status = params.get("status", "Safe Stop")
        what_happened = params.get("what_happened", "The operation could not be completed.")
        reason = params.get("reason", "An invalid parameter or data incompatibility was encountered.")
        recovery_attempted = params.get("recovery_attempted", "Evaluated alternative compatible processing strategies.")
        recovery_result = params.get("recovery_result", "No safe automatic recovery could be validated.")
        recommended_action = params.get("recommended_action", "Review dataset inputs or adjust experiment configuration.")
        ref_id = params.get("reference_id", input_data.session_id or error_id)

        panel = SafeErrorFormatter.format_user_panel(
            error_id=error_id,
            status=status,
            stage=stage,
            what_happened=what_happened,
            reason=reason,
            recovery_attempted=recovery_attempted,
            recovery_result=recovery_result,
            recommended_action=recommended_action,
            reference_id=ref_id,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=what_happened,
            data={"user_panel": panel, "error_id": error_id, "stage": stage},
        )
