"""
DataWise AI — MonitoringAgent
Monitors inference latency, throughput, error rates, and prediction distribution.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.monitoring_agent.schemas import MonitoringAgentInput, MonitoringAgentResult


class MonitoringAgent(BaseAgent):
    """MonitoringAgent: Monitors inference latency, throughput, error rates, and prediction distribution."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="MonitoringAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.monitoring.agent import MonitoringAgent as MA; return MA(session_id=input_data.session_id).analyze(input_data)
