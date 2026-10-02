"""
DataWise AI — DatasetProfilingAgent
Calculates row/col dimensions, missing percentages, cardinality, and summary distributions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.dataset_profiling_agent.schemas import DatasetProfilingAgentInput, DatasetProfilingAgentResult


class DatasetProfilingAgent(BaseAgent):
    """DatasetProfilingAgent: Calculates row/col dimensions, missing percentages, cardinality, and summary distributions."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DatasetProfilingAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.profiling.agent import ProfilingAgent; return ProfilingAgent(session_id=input_data.session_id).analyze(input_data)
