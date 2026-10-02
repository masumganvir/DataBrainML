"""
Recovery Planning Agent
Formulates strategic, verified multi-step recovery plans based on root cause diagnostics.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.error_detector import ErrorObject
from recovery.recovery_planner import RecoveryPlanner
from recovery.root_cause_analyzer import RootCauseReport


class RecoveryPlanningAgent(BaseAgent):
    """Plans targeted recovery actions avoiding blind identical retries."""

    def __init__(self, session_id: str = "", agent_name: str = "RecoveryPlanningAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        error_dict = params.get("error_obj", {})
        error_obj = ErrorObject(**error_dict) if "error_id" in error_dict else ErrorObject()

        cause_dict = params.get("root_cause", {})
        root_cause = RootCauseReport(**cause_dict) if "primary_cause" in cause_dict else RootCauseReport(
            error_id=error_obj.error_id,
            primary_cause="Generic failure",
        )

        plan = RecoveryPlanner.plan(error_obj, root_cause)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=f"Formulated plan {plan.strategy_name} ({plan.action_type})",
            data=plan.model_dump(),
        )
