"""
DataWise AI — FeatureAnalysisAgent
Analyzes variance, cardinality, and signal-to-noise ratio per feature.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.feature_analysis_agent.schemas import FeatureAnalysisAgentInput, FeatureAnalysisAgentResult


class FeatureAnalysisAgent(BaseAgent):
    """FeatureAnalysisAgent: Analyzes variance, cardinality, and signal-to-noise ratio per feature."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureAnalysisAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.feature_selection.agent import FeatureSelectionAgent; return FeatureSelectionAgent(session_id=input_data.session_id).analyze(input_data)
