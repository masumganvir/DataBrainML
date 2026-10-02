"""
DataWise AI — CrossValidationAgent
Executes stratified, grouped, or temporal cross-validation without leakage.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.cross_validation_agent.schemas import CrossValidationAgentInput, CrossValidationAgentResult


class CrossValidationAgent(BaseAgent):
    """CrossValidationAgent: Executes stratified, grouped, or temporal cross-validation without leakage."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="CrossValidationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.training.agent import TrainingAgent; return TrainingAgent(session_id=input_data.session_id).analyze(input_data)
