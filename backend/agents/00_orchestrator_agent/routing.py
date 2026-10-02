"""
DataWise AI — Agent 00: Orchestrator Routing Logic
Determines stage flow, loop conditions, and approval gates.
"""

from typing import Dict, Optional
from .schemas import OrchestrationState, StageTransition

STAGE_SEQUENCE = [
    "PROFILING",
    "QUALITY",
    "EDA",
    "OUTLIERS",
    "MISSING_VALUES",
    "PREPROCESSING",
    "FEATURE_ENGINEERING",
    "FEATURE_SELECTION",
    "LEAKAGE",
    "ML_STRATEGY",
    "TRAINING",
    "TUNING",
    "EVALUATION",
    "DEPLOYMENT",
    "REPORTING_NOTEBOOK",
    "COMPLETED",
]

MAX_LOOP_LIMITS = {
    "outlier_iterations": 3,
    "feature_selection_iterations": 3,
    "tuning_trials": 50,
    "preprocessing_retries": 2,
}


class WorkflowRouter:
    """Manages stage transitions and routing decisions."""

    @staticmethod
    def get_next_stage(state: OrchestrationState) -> StageTransition:
        curr = state.current_stage

        if curr not in STAGE_SEQUENCE:
            return StageTransition(
                from_stage=curr,
                to_stage="PROFILING",
                rationale="Initialized workflow to dataset profiling.",
            )

        idx = STAGE_SEQUENCE.index(curr)
        if idx >= len(STAGE_SEQUENCE) - 1:
            return StageTransition(
                from_stage=curr,
                to_stage="COMPLETED",
                rationale="Workflow finished all stages.",
            )

        next_s = STAGE_SEQUENCE[idx + 1]

        # Approval gates in Guided Mode
        requires_approval = False
        action = None
        if state.execution_mode == "guided":
            if next_s == "PREPROCESSING":
                requires_approval = True
                action = "Approve preprocessing plan (imputation, scaling, encoding)"
            elif next_s == "TRAINING":
                requires_approval = True
                action = "Approve recommended algorithms and candidate models"
            elif next_s == "TUNING":
                requires_approval = True
                action = "Approve hyperparameter tuning execution and budget"

        return StageTransition(
            from_stage=curr,
            to_stage=next_s,
            action_required=action,
            requires_user_approval=requires_approval,
            rationale=f"Advancing from {curr} to {next_s}.",
        )
