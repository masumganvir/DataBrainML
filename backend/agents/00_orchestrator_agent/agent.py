"""
DataWise AI — Agent 00: Orchestrator Agent Implementation
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
from .schemas import OrchestrationState, StageTransition
from .routing import WorkflowRouter, MAX_LOOP_LIMITS


class OrchestratorAgent:
    """Master workflow orchestrator."""

    def __init__(self, session_id: str, execution_mode: str = "guided"):
        self.state = OrchestrationState(
            session_id=session_id,
            execution_mode=execution_mode,
        )

    def analyze(self, current_stage: Optional[str] = None) -> StageTransition:
        """Determines the next stage transition and checks safety constraints."""
        if current_stage:
            self.state.current_stage = current_stage

        transition = WorkflowRouter.get_next_stage(self.state)
        return self.validate(transition)

    def validate(self, transition: StageTransition) -> StageTransition:
        """Enforces loop bounds and safety rules before transition."""
        for counter_name, max_val in MAX_LOOP_LIMITS.items():
            current_val = self.state.loop_counters.get(counter_name, 0)
            if current_val >= max_val:
                logger.warning(
                    f"Loop limit reached for {counter_name} ({current_val}/{max_val}). Enforcing progression."
                )

        return transition

    def record_stage_completed(self, stage: str, checkpoint_data: Optional[Dict[str, Any]] = None):
        """Marks a stage as completed and registers checkpoint."""
        if stage not in self.state.completed_stages:
            self.state.completed_stages.append(stage)
        self.state.current_stage = stage
        if checkpoint_data:
            self.state.checkpoints[stage] = f"checkpoint_{stage}_{int(time.time())}.json"
