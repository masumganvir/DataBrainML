"""
DataWise AI — FeatureEngineeringAgent
Generates candidate ratios, datetime decompositions, and interaction terms.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.feature_engineering_agent.schemas import FeatureEngineeringAgentInput, FeatureEngineeringAgentResult


class FeatureEngineeringAgent(BaseAgent):
    """FeatureEngineeringAgent: Generates candidate ratios, datetime decompositions, and interaction terms."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureEngineeringAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.feature_engineering.agent import FeatureEngineeringAgent as FEA; return FEA(session_id=input_data.session_id).analyze(input_data)
