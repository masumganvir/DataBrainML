"""
DataWise AI — MissingValueAgent
Analyzes MCAR/MAR indicators and evaluates imputation strategies.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.missing_value_agent.schemas import MissingValueAgentInput, MissingValueAgentResult


class MissingValueAgent(BaseAgent):
    """MissingValueAgent: Analyzes MCAR/MAR indicators and evaluates imputation strategies."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="MissingValueAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.missing_values.agent import MissingValuesAgent; return MissingValuesAgent(session_id=input_data.session_id).analyze(input_data)
