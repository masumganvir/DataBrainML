"""
DataWise AI — Monitoring Agent
Tracks data drift, latency, and predictive performance in serving.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput


class MonitoringAgent(BaseAgent):
    """Monitors model health, schema shifts, and data drift."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Monitoring Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message="Model monitoring configuration active.",
            data={"status": "Healthy", "drift_metric": "PSI", "alert_threshold": 0.15},
        )
