"""
DataWise AI — DuplicateDetectionAgent
Identifies exact and near-duplicate records across train and test partitions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.duplicate_detection_agent.schemas import DuplicateDetectionAgentInput, DuplicateDetectionAgentResult


class DuplicateDetectionAgent(BaseAgent):
    """DuplicateDetectionAgent: Identifies exact and near-duplicate records across train and test partitions."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DuplicateDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.data_quality.agent import DataQualityAgent; return DataQualityAgent(session_id=input_data.session_id).analyze(input_data)
