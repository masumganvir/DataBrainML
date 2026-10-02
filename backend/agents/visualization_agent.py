"""
DataWise AI — Visualization Agent
Coordinates interactive Plotly charts and physical Matplotlib PNG visualizations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.plot_exporter import export_pipeline_visualizations


class VisualizationAgent(BaseAgent):
    """Generates genuine, high-quality visualization files."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Visualization Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            out_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/visualizations"))
            target_col = params.get("target_column", df.columns[-1])
            task_type = params.get("task_type", "classification")

            plots = export_pipeline_visualizations(
                df=df,
                target_col=target_col,
                task_type=task_type,
                output_dir=out_dir,
            )

            all_files = [f for sublist in plots.values() for f in sublist]
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Generated {len(all_files)} visualization plots.",
                data={"plots_by_category": plots},
                artifacts_generated=all_files,
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
