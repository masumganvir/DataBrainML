"""
Agentic AutoML Intelligence Platform — Production Monitoring Agent
Monitors feature drift, prediction drift, and data distribution shifts over time windows.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from monitoring.drift_engine import drift_engine


class ProductionMonitoringAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ProductionMonitoringAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        baseline_data = input_data.parameters.get("baseline_data")
        current_data = input_data.parameters.get("current_data")

        if baseline_data is None or current_data is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message="Both baseline_data and current_data must be provided for drift monitoring.",
            )

        base_df = pd.DataFrame(baseline_data)
        curr_df = pd.DataFrame(current_data)

        drift_summary = drift_engine.compute_dataset_drift(base_df, curr_df)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="warning" if drift_summary["drift_detected"] else "success",
            data=drift_summary,
            summary=f"Monitoring: Drift {'DETECTED' if drift_summary['drift_detected'] else 'NOT DETECTED'}. "
                    f"Drifted features: {drift_summary['drifted_features_count']}/{drift_summary['total_features_evaluated']} (severity: {drift_summary['overall_severity']}).",
        )
