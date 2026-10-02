"""
Error Detection Agent
Monitors runtime exceptions, timeouts, and state faults, normalizing them into structured ErrorObjects.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.error_detector import ErrorDetector


class ErrorDetectionAgent(BaseAgent):
    """Detects and captures unstructured errors, normalizing them into sanitized ErrorObjects."""

    def __init__(self, session_id: str = "", agent_name: str = "ErrorDetectionAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        raw_error = params.get("error") or params.get("exception", "Execution anomaly detected")
        stage = params.get("stage", "runtime")
        agent_id = params.get("agent_id", "unspecified")
        node_id = params.get("node_id", "unspecified_node")
        attempt_count = params.get("attempt_count", 1)
        context = params.get("context", {})

        error_obj = ErrorDetector.detect_and_normalize(
            exception=raw_error,
            stage=stage,
            agent_id=agent_id,
            node_id=node_id,
            workflow_id=input_data.session_id or "default_workflow",
            attempt_count=attempt_count,
            context=context,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=f"Detected and structured error {error_obj.error_id}",
            data=error_obj.model_dump(),
        )
