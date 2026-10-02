"""
DataWise AI — ReportGenerationAgent
Compiles executive HTML, PDF, and Markdown summary reports.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.report_generation_agent.schemas import ReportGenerationAgentInput, ReportGenerationAgentResult


class ReportGenerationAgent(BaseAgent):
    """ReportGenerationAgent: Compiles executive HTML, PDF, and Markdown summary reports."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ReportGenerationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.artifact_generation.agent import ArtifactGenerationAgent; return ArtifactGenerationAgent(session_id=input_data.session_id).analyze(input_data)
