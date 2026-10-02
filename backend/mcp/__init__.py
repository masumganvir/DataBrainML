"""
Agentic AutoML Intelligence Platform — MCP Package
"""

from mcp.schemas import MCPToolCall, MCPToolDefinition, MCPToolResult
from mcp.server import MCPService, mcp_service

__all__ = [
    "MCPToolCall",
    "MCPToolDefinition",
    "MCPToolResult",
    "MCPService",
    "mcp_service",
]
