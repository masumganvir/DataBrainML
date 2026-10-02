"""
DataWise AI — ModelComparisonAgent
Compares candidates across F1, PR-AUC, ROC-AUC, latency, and stability.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.model_comparison_agent.schemas import ModelComparisonAgentInput, ModelComparisonAgentResult


class ModelComparisonAgent(BaseAgent):
    """ModelComparisonAgent: Compares candidates across F1, PR-AUC, ROC-AUC, latency, and stability."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelComparisonAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.model_comparison.agent import ModelComparisonAgent as MCA; return MCA(session_id=input_data.session_id).analyze(input_data)
