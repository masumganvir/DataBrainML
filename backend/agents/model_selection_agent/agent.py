"""
DataWise AI — ModelSelectionAgent
Selects candidate algorithms based on dataset size, feature types, and latency.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.model_selection_agent.schemas import ModelSelectionAgentInput, ModelSelectionAgentResult


class ModelSelectionAgent(BaseAgent):
    """ModelSelectionAgent: Selects candidate algorithms based on dataset size, feature types, and latency."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelSelectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.model_selection.agent import ModelSelectionAgent as MSA; return MSA(session_id=input_data.session_id).analyze(input_data)
