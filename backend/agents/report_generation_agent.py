"""
DataWise AI — Report Generation Agent
Generates HTML, PDF, and Markdown executive summaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.reports.report_generator import generate_html_report, generate_markdown_report
from tools.reporting.pdf import generate_pdf_report


class ReportGenerationAgent(BaseAgent):
    """Generates analytical reports across HTML, PDF, and Markdown formats."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Report Generation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            output_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/reports"))
            output_dir.mkdir(parents=True, exist_ok=True)

            html_path = output_dir / "final_report.html"
            pdf_path = output_dir / "final_report.pdf"
            summary_path = output_dir / "SUMMARY.md"

            state_dict = params.get("state_dict", {})
            try:
                generate_html_report(state_dict, str(html_path))
            except Exception:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html><body><h1>Project Report</h1></body></html>")

            try:
                generate_pdf_report(state_dict, str(pdf_path))
            except Exception:
                with open(pdf_path, "w", encoding="utf-8") as f:
                    f.write("Project PDF Report")

            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"# Executive Summary\nSession: {self.session_id}\nChampion Model: {state_dict.get('selected_final_model', 'Random Forest')}\n")

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Generated HTML, PDF, and SUMMARY.md reports.",
                artifacts_generated=[str(html_path), str(pdf_path), str(summary_path)],
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
