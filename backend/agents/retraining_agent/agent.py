"""
DataWise AI — RetrainingAgent
Evaluates retrained challenger models against production baselines.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.retraining_agent.schemas import RetrainingAgentInput, RetrainingAgentResult


class RetrainingAgent(BaseAgent):
    """RetrainingAgent: Evaluates retrained challenger models against production baselines."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="RetrainingAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.retraining.agent import RetrainingAgent as RA; return RA(session_id=input_data.session_id).analyze(input_data)
