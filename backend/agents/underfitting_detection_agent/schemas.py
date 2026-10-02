"""
DataWise AI — Underfitting Detection Agent Schemas (Section 27)
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UnderfittingReport(BaseModel):
    is_underfitting: bool
    train_score: float = 0.0
    val_score: float = 0.0
    score_gap: float = 0.0
    severity: str = "none"  # none, moderate, severe
    evidence: str = ""
    root_causes: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    model_name: str = ""
