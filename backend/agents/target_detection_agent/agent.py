"""
DataWise AI — TargetDetectionAgent
Infers candidate target columns based on naming heuristics and cardinality.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.target_detection_agent.schemas import TargetDetectionAgentInput, TargetDetectionAgentResult


class TargetDetectionAgent(BaseAgent):
    """TargetDetectionAgent: Infers candidate target columns based on naming heuristics and cardinality."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="TargetDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.problem_type.agent import ProblemTypeAgent; return ProblemTypeAgent(session_id=input_data.session_id).analyze(input_data)
