"""
DataWise AI — DriftDetectionAgent
Computes Population Stability Index (PSI) and feature distribution drift.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.drift_detection_agent.schemas import DriftDetectionAgentInput, DriftDetectionAgentResult


class DriftDetectionAgent(BaseAgent):
    """DriftDetectionAgent: Computes Population Stability Index (PSI) and feature distribution drift."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DriftDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.monitoring.agent import MonitoringAgent; return MonitoringAgent(session_id=input_data.session_id).analyze(input_data)
