"""
Agentic AutoML Intelligence Platform — Model Health Agent
Compiles real-time model health reports, latency quantiles, and SLA compliance.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from monitoring.health_dashboard import model_health_monitor


class ModelHealthAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelHealthAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        drift_report = input_data.parameters.get("drift_report")
        concept_drift = input_data.parameters.get("concept_drift_report")
        shadow_version = input_data.parameters.get("shadow_version")

        health_report = model_health_monitor.get_health_report(
            drift_report=drift_report,
            concept_drift_report=concept_drift,
            shadow_version=shadow_version,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if health_report.status != "critical" else "warning",
            data=health_report.model_dump(),
            summary=f"Model status: {health_report.status.upper()}. Total predictions: {health_report.total_predictions}, avg latency: {health_report.average_latency_ms}ms.",
        )
