"""
DataWise AI — Report Agent
Specialized agent for synthesizing end-to-end dataset documentation and executive reports.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.reports.report_generator import generate_html_report, generate_markdown_report
from app.state.data_science_state import DataScienceState


class ReportAgent(BaseAgent):
    """Compiles comprehensive analytical summaries, findings, and pipeline code into downloadable reports."""

    def __init__(self) -> None:
        super().__init__(
            name="ReportAgent",
            role="Technical Documentation & Reporting Specialist",
            description="Compiles analytical findings, data hygiene audits, feature decisions, and ML roadmaps into polished reports.",
            system_prompt=(
                "You are an expert technical writer and data science documentation specialist. "
                "Structure comprehensive executive summaries, methodology sections, and findings. "
                "Highlight key business takeaways, data quality risks, and clear next steps for data science teams."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Synthesizing final reports for session={state.get('session_id')}")
        try:
            generate_markdown_report(state)
            generate_html_report(state)
            return {
                **state,
                "completed_stages": [*state.get("completed_stages", []), "REPORT"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Report compilation failed: {exc}")
            return state

    def generate_markdown(self, state: DataScienceState) -> str:
        """Generates a complete Markdown report from the current state."""
        return generate_markdown_report(state)

    def generate_html(self, state: DataScienceState) -> str:
        """Generates a styled, interactive HTML report from the current state."""
        return generate_html_report(state)
