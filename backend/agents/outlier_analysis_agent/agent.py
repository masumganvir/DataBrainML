"""
DataWise AI — OutlierAnalysisAgent
Detects outliers via IQR, Modified Z-score, and Isolation Forest without blind deletion.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.outlier_analysis_agent.schemas import OutlierAnalysisAgentInput, OutlierAnalysisAgentResult


class OutlierAnalysisAgent(BaseAgent):
    """OutlierAnalysisAgent: Detects outliers via IQR, Modified Z-score, and Isolation Forest without blind deletion."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="OutlierAnalysisAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.outlier.agent import OutlierAgent; return OutlierAgent(session_id=input_data.session_id).analyze(input_data)
