"""
DataWise AI — FeatureSelectionAgent
Performs variance, mutual information, and recursive feature elimination.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.feature_selection_agent.schemas import FeatureSelectionAgentInput, FeatureSelectionAgentResult


class FeatureSelectionAgent(BaseAgent):
    """FeatureSelectionAgent: Performs variance, mutual information, and recursive feature elimination."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureSelectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.feature_selection.agent import FeatureSelectionAgent as FSA; return FSA(session_id=input_data.session_id).analyze(input_data)
