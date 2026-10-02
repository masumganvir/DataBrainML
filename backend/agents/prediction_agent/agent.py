"""
DataWise AI — PredictionAgent
Performs fast, schema-validated inference with confidence scores.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.prediction_agent.schemas import PredictionAgentInput, PredictionAgentResult


class PredictionAgent(BaseAgent):
    """PredictionAgent: Performs fast, schema-validated inference with confidence scores."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="PredictionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.deployment.agent import DeploymentAgent; return DeploymentAgent(session_id=input_data.session_id).analyze(input_data)
