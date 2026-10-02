"""
DataWise AI — Supervisor Agent Schemas
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowPlan(BaseModel):
    objective: str
    problem_type: str = "classification"
    selected_agents: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    loop_limits: Dict[str, int] = Field(default_factory=lambda: {
        "outlier_refinement": 2,
        "feature_selection_tuning": 2,
        "model_retraining": 3,
        "hyperparameter_trials": 20,
    })
    current_step_index: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    is_completed: bool = False
    pending_approval: Optional[str] = None
