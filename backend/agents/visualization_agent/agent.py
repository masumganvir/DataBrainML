"""
DataWise AI — VisualizationAgent
Generates interactive Plotly and Matplotlib charts (histograms, heatmaps, boxplots).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.visualization_agent.schemas import VisualizationAgentInput, VisualizationAgentResult


class VisualizationAgent(BaseAgent):
    """VisualizationAgent: Generates interactive Plotly and Matplotlib charts (histograms, heatmaps, boxplots)."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="VisualizationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.visualization.agent import VisualizationAgent as VA; return VA(session_id=input_data.session_id).analyze(input_data)
