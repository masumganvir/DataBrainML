"""
DataWise AI — Profiling Agent
Computes comprehensive dataset profiles and coordinates YData/fallback profiling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.profiler import DatasetProfiler
from app.tools.profiling_reporter import generate_dataset_profile_artifacts


class ProfilingAgent(BaseAgent):
    """Generates detailed statistical profile and HTML artifacts."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Profiling Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            out_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/profiling"))
            artifacts = generate_dataset_profile_artifacts(df, out_dir)

            profiler = DatasetProfiler(df)
            profile_data = profiler.profile()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Profiled {len(df.columns)} columns.",
                data={"profile": profile_data, "artifacts": artifacts},
                artifacts_generated=[artifacts["html_path"], artifacts["json_path"]],
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
