"""
Agentic AutoML Intelligence Platform — Rollback Agent
Safely restores previous stable model checkpoints with audit trail generation.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from deployment.shadow_manager import deployment_manager


class RollbackAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="RollbackAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        target_version = input_data.parameters.get("target_version")
        reason = input_data.parameters.get("reason", "Manual or automated drift triggered rollback")

        try:
            previous_active = deployment_manager.active_version
            restored_version = deployment_manager.rollback(target_version=target_version)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "previous_version": previous_active,
                    "restored_version": restored_version,
                    "reason": reason,
                },
                summary=f"Rollback successful: Restored '{restored_version}' replacing '{previous_active}'. Reason: {reason}",
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message=f"Rollback failed: {str(e)}",
            )
