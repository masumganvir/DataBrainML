"""
DataWise AI — Agent: Data Quality Agent Schemas
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    session_id: str
    dataset_path: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    session_id: str
    agent_name: str = "Data Quality Agent"
    status: str = "success"
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: str
    warnings: List[str] = Field(default_factory=list)
