"""
DataWise AI — Fallback Agent
Handles stage exceptions gracefully, determining fallback routes without confidential disclosure.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from agents.base import BaseAgent, AgentInput, AgentOutput


class FallbackAgent(BaseAgent):
    """Graceful degradation and fallback coordinator."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Fallback Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        failed_stage = params.get("failed_stage", "unknown")
        error_msg = params.get("error", "General execution error")

        logger.warning(f"FallbackAgent activated for stage '{failed_stage}': {error_msg}")
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="warning",
            message=f"Fallback recovery executed for {failed_stage}.",
            data={"recovered": True, "failed_stage": failed_stage, "fallback_strategy": "robust_default"},
        )
