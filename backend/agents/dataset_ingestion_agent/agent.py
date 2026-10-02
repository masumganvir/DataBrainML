"""
DataWise AI — DatasetIngestionAgent
Validates MIME types, extensions, checksums, and safely loads dataset files.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.dataset_ingestion_agent.schemas import DatasetIngestionAgentInput, DatasetIngestionAgentResult


class DatasetIngestionAgent(BaseAgent):
    """DatasetIngestionAgent: Validates MIME types, extensions, checksums, and safely loads dataset files."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DatasetIngestionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.intake.agent import IntakeAgent; return IntakeAgent(session_id=input_data.session_id).analyze(input_data)
