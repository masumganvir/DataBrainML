"""
Agentic AutoML Intelligence Platform — Schema Discovery Agent
Introspects tables, columns, data types, keys, relationships, and candidate targets.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from connectors.registry import ConnectorRegistry


class SchemaDiscoveryAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="SchemaDiscoveryAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        source_type = input_data.parameters.get("source_type", "sqlite")
        connection_uri = input_data.parameters.get("connection_uri", "")

        try:
            connector = ConnectorRegistry.get_connector(source_type=source_type, connection_uri=connection_uri)
            schema_profile = connector.discover_schema()

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=schema_profile.model_dump(),
                summary=f"Discovered {schema_profile.total_tables} tables, {schema_profile.total_columns} columns. "
                        f"Candidate targets: {schema_profile.candidate_targets}.",
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message=f"Schema discovery error: {str(e)}",
            )
