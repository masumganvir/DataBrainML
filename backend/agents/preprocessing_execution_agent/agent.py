"""
DataWise AI — PreprocessingExecutionAgent
Executes data transformations and builds reproducible Scikit-Learn Pipelines.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.preprocessing_execution_agent.schemas import PreprocessingExecutionAgentInput, PreprocessingExecutionAgentResult


class PreprocessingExecutionAgent(BaseAgent):
    """PreprocessingExecutionAgent: Executes data transformations and builds reproducible Scikit-Learn Pipelines."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="PreprocessingExecutionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.scaling.agent import ScalingAgent; return ScalingAgent(session_id=input_data.session_id).analyze(input_data)
