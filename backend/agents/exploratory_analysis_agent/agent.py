"""
DataWise AI — ExploratoryAnalysisAgent
Analyzes correlations, pairwise interactions, and multivariate patterns.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.exploratory_analysis_agent.schemas import ExploratoryAnalysisAgentInput, ExploratoryAnalysisAgentResult


class ExploratoryAnalysisAgent(BaseAgent):
    """ExploratoryAnalysisAgent: Analyzes correlations, pairwise interactions, and multivariate patterns."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ExploratoryAnalysisAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.visualization.agent import VisualizationAgent; return VisualizationAgent(session_id=input_data.session_id).analyze(input_data)
