"""
DataWise AI — DuplicateDetectionAgent Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DuplicateDetectionAgentInput(BaseModel):
    session_id: str = ""
    dataset_path: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class DuplicateDetectionAgentResult(BaseModel):
    status: str = "success"
    summary: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
