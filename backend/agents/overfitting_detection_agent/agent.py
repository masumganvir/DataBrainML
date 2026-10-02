"""
DataWise AI — OverfittingDetectionAgent
Identifies train-validation score divergence, high variance, and memorization.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.overfitting_detection_agent.schemas import OverfittingDetectionAgentInput, OverfittingDetectionAgentResult


class OverfittingDetectionAgent(BaseAgent):
    """OverfittingDetectionAgent: Identifies train-validation score divergence, high variance, and memorization."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="OverfittingDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.overfitting_detection.agent import OverfittingDetectionAgent as ODA; return ODA(session_id=input_data.session_id).analyze(input_data)
