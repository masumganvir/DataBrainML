"""
DataWise AI — DriftDetectionAgent Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DriftDetectionAgentInput(BaseModel):
    session_id: str = ""
    dataset_path: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DriftDetectionAgentResult(BaseModel):
    status: str = "success"
    summary: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
