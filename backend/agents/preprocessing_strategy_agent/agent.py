"""
DataWise AI — PreprocessingStrategyAgent
Recommends ColumnTransformer strategies tailored to problem and distribution.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.preprocessing_strategy_agent.schemas import PreprocessingStrategyAgentInput, PreprocessingStrategyAgentResult


class PreprocessingStrategyAgent(BaseAgent):
    """PreprocessingStrategyAgent: Recommends ColumnTransformer strategies tailored to problem and distribution."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="PreprocessingStrategyAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.encoding.agent import EncodingAgent; return EncodingAgent(session_id=input_data.session_id).analyze(input_data)
