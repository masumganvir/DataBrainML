"""
DataWise AI — DataQualityAgent
Audits missingness, duplicate rows, constant columns, and calculates health scores.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.data_quality_agent.schemas import DataQualityAgentInput, DataQualityAgentResult


class DataQualityAgent(BaseAgent):
    """DataQualityAgent: Audits missingness, duplicate rows, constant columns, and calculates health scores."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DataQualityAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.data_quality.agent import DataQualityAgent as DQA; return DQA(session_id=input_data.session_id).analyze(input_data)
