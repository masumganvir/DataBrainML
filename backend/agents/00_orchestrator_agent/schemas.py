"""
DataWise AI — Agent 00: Orchestrator Agent
Controls the entire workflow, manages state transitions, checkpoints, loop controls, and human approvals.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrchestrationState(BaseModel):
    session_id: str
    current_stage: str = "INGEST"
    execution_mode: str = "guided"  # "guided" | "autonomous"
    completed_stages: List[str] = Field(default_factory=list)
    pending_approval: Optional[Dict[str, Any]] = None
    loop_counters: Dict[str, int] = Field(default_factory=lambda: {
        "outlier_iterations": 0,
        "feature_selection_iterations": 0,
        "tuning_trials": 0,
        "preprocessing_retries": 0,
    })
    checkpoints: Dict[str, str] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class StageTransition(BaseModel):
    from_stage: str
    to_stage: str
    action_required: Optional[str] = None
    requires_user_approval: bool = False
    rationale: str
