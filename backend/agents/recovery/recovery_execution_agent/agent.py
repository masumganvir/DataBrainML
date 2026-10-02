"""
Recovery Execution Agent
Executes recovery plans and validates recovered objects before proceeding.
"""

from __future__ import annotations

from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.error_detector import ErrorObject
from recovery.recovery_executor import RecoveryExecutor
from recovery.recovery_planner import RecoveryPlan


class RecoveryExecutionAgent(BaseAgent):
    """Executes recovery plans and triggers independent validation."""

    def __init__(self, session_id: str = "", agent_name: str = "RecoveryExecutionAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        plan_dict = params.get("plan", {})
        plan = RecoveryPlan(**plan_dict) if "strategy_name" in plan_dict else RecoveryPlan(
            error_id="ERR-UNKNOWN",
            strategy_name="PRESERVATION_SAFE_STOP",
            action_type="SAFE_STOP",
            confidence="LOW",
        )

        error_dict = params.get("error_obj", {})
        error_obj = ErrorObject(**error_dict) if "error_id" in error_dict else ErrorObject()

        state = params.get("system_state") or input_data.state_ref or {}

        decision, updated_state, val_rep = RecoveryExecutor.execute_plan(plan, error_obj, state)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if val_rep.is_valid else "warning",
            summary=f"Executed recovery strategy {plan.strategy_name}: {decision.value}",
            data={
                "decision": decision.value,
                "is_valid": val_rep.is_valid,
                "validation_message": val_rep.validation_message,
                "updated_state": updated_state if val_rep.is_valid else None,
            },
        )
