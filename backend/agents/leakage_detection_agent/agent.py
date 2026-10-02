"""
DataWise AI — LeakageDetectionAgent
Checks for target leakage, train/test contamination, and post-outcome features.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.leakage_detection_agent.schemas import LeakageDetectionAgentInput, LeakageDetectionAgentResult


class LeakageDetectionAgent(BaseAgent):
    """LeakageDetectionAgent: Checks for target leakage, train/test contamination, and post-outcome features."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="LeakageDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.leakage_detection.agent import LeakageDetectionAgent as LDA; return LDA(session_id=input_data.session_id).analyze(input_data)
