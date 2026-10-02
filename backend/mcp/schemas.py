"""
Agentic AutoML Intelligence Platform — MCP (Model Context Protocol) Schemas
Defines agent tool interaction contracts for secure database and metadata operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class MCPToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
