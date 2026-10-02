"""
Rollback Agent (Recovery Suite)
Reverts pipeline execution to the nearest safe LangGraph checkpoint without unnecessary complete restarts.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.rollback_manager import RollbackManager


class RollbackAgent(BaseAgent):
    """Retrieves safe state checkpoints to restore execution after unrecoverable node errors."""

    def __init__(self, session_id: str = "", agent_name: str = "RollbackAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)
        self.rollback_manager = RollbackManager()

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        workflow_id = input_data.session_id or params.get("workflow_id", "default_workflow")
        failed_stage = params.get("failed_stage", "evaluation")

        checkpoint = self.rollback_manager.get_nearest_safe_checkpoint(workflow_id, failed_stage)

        if checkpoint:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                summary=f"Rolled back to safe checkpoint: {checkpoint.checkpoint_id} ({checkpoint.stage_name})",
                data={
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "stage_name": checkpoint.stage_name,
                    "timestamp": checkpoint.timestamp,
                    "state_payload": checkpoint.state_payload,
                },
            )
        else:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                summary="No previous checkpoint found. Returning initial baseline state.",
                data={"checkpoint_id": "checkpoint_1_data_loaded", "stage_name": "data_ingestion"},
            )
