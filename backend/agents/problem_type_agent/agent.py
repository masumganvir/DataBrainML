"""
DataWise AI — ProblemTypeAgent
Identifies classification, regression, clustering, or anomaly detection tasks.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.problem_type_agent.schemas import ProblemTypeAgentInput, ProblemTypeAgentResult


class ProblemTypeAgent(BaseAgent):
    """ProblemTypeAgent: Identifies classification, regression, clustering, or anomaly detection tasks."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ProblemTypeAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.problem_type.agent import ProblemTypeAgent as PTA; return PTA(session_id=input_data.session_id).analyze(input_data)
