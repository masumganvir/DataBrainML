"""
DataWise AI — DataTypeAgent
Classifies columns into numerical, categorical, datetime, text, or identifier types.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.data_type_agent.schemas import DataTypeAgentInput, DataTypeAgentResult


class DataTypeAgent(BaseAgent):
    """DataTypeAgent: Classifies columns into numerical, categorical, datetime, text, or identifier types."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DataTypeAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.profiling.agent import ProfilingAgent; return ProfilingAgent(session_id=input_data.session_id).analyze(input_data)
