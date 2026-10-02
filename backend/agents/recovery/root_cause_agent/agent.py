"""
Root Cause Agent
Conducts evidence-based diagnostic analysis without inventing root causes.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.error_detector import ErrorObject
from recovery.root_cause_analyzer import RootCauseAnalyzer


class RootCauseAgent(BaseAgent):
    """Analyzes runtime and context state to diagnose verified causes."""

    def __init__(self, session_id: str = "", agent_name: str = "RootCauseAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        error_dict = params.get("error_obj") or params
        error_obj = ErrorObject(**error_dict) if isinstance(error_dict, dict) and "error_id" in error_dict else ErrorObject(
            message=str(error_dict)
        )
        system_state = params.get("system_state") or input_data.state_ref or {}

        report = RootCauseAnalyzer.analyze(error_obj, system_state)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=f"Diagnosed cause: {report.primary_cause} (Confidence: {report.confidence})",
            data=report.model_dump(),
        )
