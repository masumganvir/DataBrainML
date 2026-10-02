"""
DataWise AI — BaselineTrainingAgent
Establishes a simple, fast, reproducible baseline model.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.baseline_training_agent.schemas import BaselineTrainingAgentInput, BaselineTrainingAgentResult


class BaselineTrainingAgent(BaseAgent):
    """BaselineTrainingAgent: Establishes a simple, fast, reproducible baseline model."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="BaselineTrainingAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.training.agent import TrainingAgent; return TrainingAgent(session_id=input_data.session_id).analyze(input_data)
