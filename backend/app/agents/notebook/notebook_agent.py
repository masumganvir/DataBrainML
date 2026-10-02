"""
DataWise AI — Notebook Agent
Generates comprehensive, standalone reproducible Jupyter Notebooks (.ipynb).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.notebook_generator import JupyterNotebookGenerator


class NotebookAgent(BaseAgent):
    """
    Synthesizes a 24-section executable Jupyter Notebook (.ipynb) capturing the full
    reproducible analytical trajectory from EDA to model serialization.
    """

    def __init__(self) -> None:
        super().__init__(
            name="NotebookAgent",
            role="Jupyter Notebook & Reproducibility Specialist",
            description="Compiles an executable 24-section Jupyter Notebook (.ipynb) containing real Python cells for exploratory analysis, preprocessing, cross-validation, and inference.",
            system_prompt=(
                "You are an expert computational notebook engineer. "
                "Ensure that all generated code cells are fully executable, properly sequenced, "
                "and maintain strict consistency with the analytical report and serialized pipeline."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        session_id = state.get("session_id", "default_session")
        logger.info(f"[{self.name}] Generating Jupyter Notebook for session={session_id}")

        try:
            generator = JupyterNotebookGenerator(session_id=session_id, state=state)
            nb_path = generator.build_notebook()

            return {
                **state,
                "notebook_path": nb_path,
                "current_stage": "REPORTING",
                "completed_stages": [*state.get("completed_stages", []), "NOTEBOOK_GENERATION"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Notebook generation failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "NOTEBOOK_GENERATION", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        nb_path = state.get("notebook_path")
        return f"Jupyter Notebook generated: {nb_path}" if nb_path else "No notebook generated yet."
