"""
DataWise AI — Pipeline Builder Agent
Specialized agent for generating clean Scikit-Learn ColumnTransformers, Pipelines, and reproducible scripts.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.pipeline_builder import PipelineBuilder


class PipelineBuilderAgent(BaseAgent):
    """Builds robust Scikit-Learn ColumnTransformer and Pipeline objects with executable code export."""

    def __init__(self) -> None:
        super().__init__(
            name="PipelineBuilderAgent",
            role="Production ML Pipeline Engineer",
            description="Compiles imputation, encoding, and scaling steps into reproducible, leakage-free Scikit-Learn pipelines.",
            system_prompt=(
                "You are an expert Scikit-Learn engineer. "
                "Structure end-to-end preprocessing pipelines using ColumnTransformer, Pipeline, and custom transformers. "
                "Ensure that transformations only fit on training splits to prevent data leakage. "
                "Provide clean, PEP-8 compliant Python code ready to copy-paste into production."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Constructing Scikit-Learn pipeline for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        try:
            builder = PipelineBuilder(
                df,
                target_column=state.get("target_column"),
                task_type=state.get("task_type"),
                encoding_plan=state.get("encoding_plan", []),
                scaling_plan=state.get("scaling_plan", []),
                transformation_plan=state.get("transformation_plan", []),
                selected_features=state.get("selected_features"),
            )
            definition = builder.build()
            return {
                **state,
                "pipeline_definition": definition,
                "generated_pipeline_code": definition.get("generated_code", ""),
                "current_stage": "ML_RECOMMENDATION",
                "completed_stages": [*state.get("completed_stages", []), "PIPELINE_BUILDING"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Pipeline construction failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "PIPELINE_BUILDING", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        code = state.get("generated_pipeline_code", "")
        return f"Generated Pipeline Code Length: {len(code)} characters.\nPreview:\n{code[:300]}..."
