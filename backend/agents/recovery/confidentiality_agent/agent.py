"""
Confidentiality Agent
Inspects outputs, reports, code, and errors before they leave the internal system,
enforcing absolute secret redaction, PII protection, and prompt defense.
"""

from __future__ import annotations

from typing import Any, Dict
from agents.base import AgentInput, AgentOutput, BaseAgent
from recovery.context_sanitizer import OutputSecurityGate


class ConfidentialityAgent(BaseAgent):
    """Guarantees zero leakage of credentials, PII, tracebacks, or private system prompts."""

    def __init__(self, session_id: str = "", agent_name: str = "ConfidentialityAgent"):
        super().__init__(session_id=session_id, agent_name=agent_name)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters
        content_type = params.get("content_type", "general")
        raw_content = params.get("content", "")

        is_safe, violations = OutputSecurityGate.validate_safety(raw_content)

        if content_type == "notebook":
            sanitized = OutputSecurityGate.sanitize_notebook(raw_content)
        elif content_type == "code":
            sanitized = OutputSecurityGate.sanitize_code(str(raw_content))
        elif content_type == "report":
            sanitized = OutputSecurityGate.sanitize_report(str(raw_content))
        else:
            sanitized = OutputSecurityGate.sanitize(raw_content)

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            summary=f"Confidentiality inspection complete ({len(violations)} violations redacted)",
            data={
                "was_safe": is_safe,
                "violations_found": violations,
                "sanitized_content": sanitized,
            },
        )
