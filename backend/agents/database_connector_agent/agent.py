"""
Agentic AutoML Intelligence Platform — Database Connector Agent
Manages external database connections, credentials validation, and health checks.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from connectors.registry import ConnectorRegistry


class DatabaseConnectorAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DatabaseConnectorAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        source_type = input_data.parameters.get("source_type", "sqlite")
        connection_uri = input_data.parameters.get("connection_uri", "")

        if not connection_uri:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message="Missing 'connection_uri' in parameters.",
            )

        try:
            connector = ConnectorRegistry.get_connector(
                source_type=source_type,
                connection_uri=connection_uri,
            )
            test_res = connector.test_connection()

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success" if test_res.success else "error",
                data=test_res.model_dump(),
                summary=f"Database test for {source_type}: {test_res.message} (latency: {test_res.latency_ms}ms)",
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message=f"Connector failure: {str(e)}",
            )
