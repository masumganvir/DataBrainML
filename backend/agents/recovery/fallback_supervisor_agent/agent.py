"""
Fallback Supervisor Agent
Master agent coordinating the recovery lifecycle for any failed agent or workflow.
"""

from __future__ import annotations

from typing import Any, Dict
from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.recovery_supervisor import FallbackRecoverySupervisor


class FallbackSupervisorAgent(BaseAgent):
    """Coordinates detection, diagnosis, recovery, and validation for agent failures."""

    def __init__(self, session_id: str = "", agent_name: str = "FallbackSupervisorAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)
        self.supervisor = FallbackRecoverySupervisor()

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        raw_error = params.get("error") or params.get("exception", "Unknown agent failure")
        stage = params.get("stage", "agent_execution")
        agent_id = params.get("agent_id", "unspecified_agent")
        attempt_count = params.get("attempt_count", 1)
        system_state = params.get("system_state") or input_data.state_ref or {}

        result = self.supervisor.handle_failure(
            exception=raw_error,
            stage=stage,
            agent_id=agent_id,
            workflow_id=input_data.session_id or "default_workflow",
            attempt_count=attempt_count,
            system_state=system_state,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if result.success else "warning",
            summary=result.safe_message,
            data={
                "decision": result.decision.value,
                "error_id": result.error_id,
                "safe_message": result.safe_message,
                "user_panel": result.user_panel,
                "api_response": result.api_response,
                "retry_delay_seconds": result.retry_delay_seconds,
                "checkpoint_resumed": result.checkpoint_resumed,
                "recovered_state": result.recovered_state,
            },
        )
