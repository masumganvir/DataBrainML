"""
DataWise AI — ExplainabilityAgent
Calculates global and local SHAP feature attributions and permutation importance.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.explainability_agent.schemas import ExplainabilityAgentInput, ExplainabilityAgentResult


class ExplainabilityAgent(BaseAgent):
    """ExplainabilityAgent: Calculates global and local SHAP feature attributions and permutation importance."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ExplainabilityAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.explainability.agent import ExplainabilityAgent as EA; return EA(session_id=input_data.session_id).analyze(input_data)
