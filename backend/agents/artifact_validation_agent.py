"""
DataWise AI — Artifact Validation Agent
Verifies existence, loadability, and functional correctness of all artifacts.
"""

from __future__ import annotations

from pathlib import Path
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.artifact_validation import ArtifactValidationAgent as QAEngine


class ArtifactValidationAgent(BaseAgent):
    """Quality assurance agent verifying all generated artifacts."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Artifact Validation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        run_dir_str = params.get("run_dir") or f"artifacts/{self.session_id}"
        run_dir = Path(run_dir_str)

        qa = QAEngine(run_dir)
        results = qa.validate_all(sample_input=params.get("sample_input"))

        status = "success" if results["all_passed"] else ("warning" if len(results["errors"]) == 0 else "error")
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status=status,
            message="Artifacts validated successfully." if results["all_passed"] else "Artifact validation completed with warnings/errors.",
            data=results,
        )
