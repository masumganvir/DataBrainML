"""
DataWise AI — RobustnessAgent
Tests prediction stability against feature perturbations and noise injection.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.robustness_agent.schemas import RobustnessAgentInput, RobustnessAgentResult


class RobustnessAgent(BaseAgent):
    """RobustnessAgent: Tests prediction stability against feature perturbations and noise injection."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="RobustnessAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.robustness.agent import RobustnessAgent as RA; return RA(session_id=input_data.session_id).analyze(input_data)
