"""
DataWise AI — NotebookGenerationAgent
Generates fully executable 26-section Jupyter notebooks with markdown documentation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.notebook_generation_agent.schemas import NotebookGenerationAgentInput, NotebookGenerationAgentResult


class NotebookGenerationAgent(BaseAgent):
    """NotebookGenerationAgent: Generates fully executable 26-section Jupyter notebooks with markdown documentation."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="NotebookGenerationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.artifact_generation.agent import ArtifactGenerationAgent; return ArtifactGenerationAgent(session_id=input_data.session_id).analyze(input_data)
