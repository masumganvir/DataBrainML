"""
DataWise AI — DeploymentAgent
Packages trained pipelines into FastAPI prediction endpoints and Docker specs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.deployment_agent.schemas import DeploymentAgentInput, DeploymentAgentResult


class DeploymentAgent(BaseAgent):
    """DeploymentAgent: Packages trained pipelines into FastAPI prediction endpoints and Docker specs."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DeploymentAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.deployment.agent import DeploymentAgent as DA; return DA(session_id=input_data.session_id).analyze(input_data)
