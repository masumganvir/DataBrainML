"""
Agentic AutoML Intelligence Platform — Database Security Agent
Validates connection security, query sanitization, and blocks destructive SQL commands.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from connectors.security import DatabaseSecurityValidator


class DatabaseSecurityAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DatabaseSecurityAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        query = input_data.parameters.get("sql_query", "")
        max_rows = input_data.parameters.get("max_rows", 50000)

        if not query:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message="No query provided for security validation.",
            )

        val = DatabaseSecurityValidator.validate_query(query, max_rows=max_rows)

        if val.is_safe:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=val.model_dump(),
                summary="Query passed read-only security checks and is authorized.",
            )
        else:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                data=val.model_dump(),
                summary=f"Security violation: {val.violation_reason}",
                warnings=[val.violation_reason or "Unsafe query"],
            )
