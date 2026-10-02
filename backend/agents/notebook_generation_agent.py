"""
DataWise AI — Notebook Generation Agent
Generates comprehensive, runnable, self-contained Jupyter notebook artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput
from tools.notebook.generator import NotebookGenerator


class NotebookGenerationAgent(BaseAgent):
    """Generates executable Jupyter notebook artifacts."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Notebook Generation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            output_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/notebook"))
            output_dir.mkdir(parents=True, exist_ok=True)
            nb_path = output_dir / "complete_ml_pipeline.ipynb"

            state_dict = {
                "dataset_path": params.get("dataset_path"),
                "target_column": params.get("target_column"),
                "ml_task_type": params.get("task_type", "classification"),
                "selected_final_model": params.get("model_name", "RandomForestClassifier"),
            }

            gen = NotebookGenerator(state_dict, project_name=f"Project_{self.session_id}")
            gen.generate(str(nb_path))

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Generated executable Jupyter notebook: {nb_path.name}",
                data={"notebook_path": str(nb_path)},
                artifacts_generated=[str(nb_path)],
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
