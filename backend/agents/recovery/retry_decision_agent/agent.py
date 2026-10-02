"""
Retry Decision Agent
Enforces bounded retry budgets, backoff delays, loop prevention, and circuit breakers.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.retry_manager import RetryManager


class RetryDecisionAgent(BaseAgent):
    """Governs retry eligibility, prevents infinite loops, and computes backoff delays."""

    def __init__(self, session_id: str = "", agent_name: str = "RetryDecisionAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)
        self.retry_manager = RetryManager()

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        workflow_id = input_data.session_id or params.get("workflow_id", "default_workflow")
        agent_id = params.get("agent_id", "unspecified")
        error_signature = params.get("error_signature", "unknown_error")
        strategy_name = params.get("strategy_name", "default_strategy")
        attempt_count = params.get("attempt_count", 1)

        is_allowed, decision_state, reason = self.retry_manager.evaluate_retry_eligibility(
            workflow_id=workflow_id,
            agent_id=agent_id,
            error_signature=error_signature,
            strategy_name=strategy_name,
            attempt_count=attempt_count,
        )

        backoff_delay = self.retry_manager.calculate_backoff(attempt_count) if is_allowed else 0.0

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if is_allowed else "warning",
            summary=f"Retry decision: {decision_state.value} ({reason})",
            data={
                "allowed": is_allowed,
                "decision_state": decision_state.value,
                "reason": reason,
                "backoff_delay_seconds": backoff_delay,
                "attempt_count": attempt_count,
            },
        )
