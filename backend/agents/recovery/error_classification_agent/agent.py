"""
Error Classification Agent
Determines failure category, assigns severity levels, and identifies retryable boundaries.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.error_classifier import ErrorClassifier
from recovery.error_detector import ErrorObject


class ErrorClassificationAgent(BaseAgent):
    """Categorizes normalized error objects and evaluates recoverability."""

    def __init__(self, session_id: str = "", agent_name: str = "ErrorClassificationAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        error_dict = params.get("error_obj") or params
        error_obj = ErrorObject(**error_dict) if isinstance(error_dict, dict) and "error_id" in error_dict else ErrorObject(
            message=str(error_dict)
        )

        classified = ErrorClassifier.classify(error_obj)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=f"Classified error as {classified.category.value} ({classified.severity.value})",
            data=classified.model_dump(),
        )
