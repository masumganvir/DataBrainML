"""
Agentic AutoML Intelligence Platform — MCP Tool Service
Provides agent tool execution layer for database discovery and safe metadata access.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from loguru import logger
import pandas as pd

from mcp.schemas import MCPToolCall, MCPToolDefinition, MCPToolResult
from connectors.registry import ConnectorRegistry
from connectors.security import DatabaseSecurityValidator


class MCPService:
    """Model Context Protocol (MCP) server for agent-driven schema discovery & safe query tools."""

    def __init__(self):
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
    ):
        self._tools[name] = MCPToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
        )
        self._handlers[name] = handler

    def list_tools(self) -> List[MCPToolDefinition]:
        return list(self._tools.values())

    def execute_tool(self, call: MCPToolCall) -> MCPToolResult:
        start_time = time.perf_counter()
        handler = self._handlers.get(call.tool_name)
        if not handler:
            return MCPToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"MCP Tool '{call.tool_name}' not found.",
                execution_time_ms=0.0,
            )

        try:
            result_data = handler(**call.arguments)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return MCPToolResult(
                tool_name=call.tool_name,
                success=True,
                data=result_data,
                execution_time_ms=round(elapsed_ms, 2),
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"[MCPService] Tool '{call.tool_name}' failed: {e}")
            return MCPToolResult(
                tool_name=call.tool_name,
                success=False,
                error=str(e),
                execution_time_ms=round(elapsed_ms, 2),
            )

    def _register_default_tools(self):
        # Tool 1: discover_schema
        self.register_tool(
            name="mcp_discover_schema",
            description="Discover tables, columns, constraints, and candidate target columns for a data source.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_type": {"type": "string", "description": "e.g. postgresql, mysql, sqlite"},
                    "connection_uri": {"type": "string", "description": "Database connection URI"},
                },
                "required": ["source_type", "connection_uri"],
            },
            handler=self._tool_discover_schema,
        )

        # Tool 2: sample_table
        self.register_tool(
            name="mcp_sample_table",
            description="Extract a read-only sample dataframe (max 1000 rows) from a table for profiling.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_type": {"type": "string"},
                    "connection_uri": {"type": "string"},
                    "table_name": {"type": "string"},
                    "limit": {"type": "integer", "default": 100},
                },
                "required": ["source_type", "connection_uri", "table_name"],
            },
            handler=self._tool_sample_table,
        )

        # Tool 3: execute_approved_query
        self.register_tool(
            name="mcp_execute_approved_query",
            description="Execute an approved, validated read-only SQL SELECT query with safety row limits.",
            input_schema={
                "type": "object",
                "properties": {
                    "source_type": {"type": "string"},
                    "connection_uri": {"type": "string"},
                    "sql_query": {"type": "string"},
                    "max_rows": {"type": "integer", "default": 500},
                },
                "required": ["source_type", "connection_uri", "sql_query"],
            },
            handler=self._tool_execute_approved_query,
        )

    def _tool_discover_schema(self, source_type: str, connection_uri: str) -> Dict[str, Any]:
        connector = ConnectorRegistry.get_connector(source_type=source_type, connection_uri=connection_uri)
        profile = connector.discover_schema()
        return profile.model_dump()

    def _tool_sample_table(self, source_type: str, connection_uri: str, table_name: str, limit: int = 100) -> Dict[str, Any]:
        connector = ConnectorRegistry.get_connector(source_type=source_type, connection_uri=connection_uri)
        df = connector.sample_table(table_name=table_name, limit=limit)
        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_records": df.head(10).to_dict(orient="records"),
        }

    def _tool_execute_approved_query(self, source_type: str, connection_uri: str, sql_query: str, max_rows: int = 500) -> Dict[str, Any]:
        val = DatabaseSecurityValidator.validate_query(sql_query, max_rows=max_rows)
        if not val.is_safe:
            raise PermissionError(f"Security validation blocked query: {val.violation_reason}")

        connector = ConnectorRegistry.get_connector(source_type=source_type, connection_uri=connection_uri)
        # Using connector engine if SQL
        if hasattr(connector, "engine"):
            import pandas as pd
            from sqlalchemy import text
            with connector.engine.connect() as conn:
                df = pd.read_sql_query(text(val.sanitized_query), conn)
                return {
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "records": df.to_dict(orient="records"),
                }
        else:
            raise NotImplementedError(f"Raw query execution is only supported for relational SQL connectors.")


mcp_service = MCPService()
