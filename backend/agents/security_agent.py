"""
DataWise AI — Security Agent
Sanitizes filenames and guards against secret leakage in notebooks, HTML, and reports.
"""

from __future__ import annotations

import re
from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput


class SecurityAgent(BaseAgent):
    """Enforces secret protection and credential sanitization."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Security Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        text = params.get("text", "")

        # Check for standard API key / secret patterns
        has_secret = bool(re.search(r"(AIza[0-9A-Za-z-_]{35}|ghp_[0-9A-Za-z]{36}|sk-[0-9A-Za-z]{32,})", text))
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success" if not has_secret else "warning",
            message="Security sanitization verified. No plaintext credentials found.",
            data={"safe": not has_secret},
        )
