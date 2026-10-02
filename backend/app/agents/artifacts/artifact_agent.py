"""
DataWise AI — Artifact Manager Agent
Serializes the production pipeline, generates metadata & scripts, and builds the ZIP project bundle.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.artifact_packager import ArtifactPackager


class ArtifactManagerAgent(BaseAgent):
    """
    Manages final pipeline serialization, metadata capture, standalone script synthesis,
    and downloadable ZIP project bundle creation.
    """

    def __init__(self) -> None:
        super().__init__(
            name="ArtifactManagerAgent",
            role="Production Packaging & Artifact Specialist",
            description="Serializes the final Pipeline artifact, records environment metadata, creates inference/preprocessing scripts, and builds downloadable project bundles.",
            system_prompt=(
                "You are an expert production ML deployment engineer. "
                "Ensure serialized artifacts are directly loadable and executable without external training dependencies. "
                "Package standalone inference scripts that validate schema and return predictions cleanly."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        session_id = state.get("session_id", "default_session")
        logger.info(f"[{self.name}] Packaging production artifacts for session={session_id}")

        try:
            packager = ArtifactPackager(session_id=session_id)

            target_col = state.get("target_column", "target")
            task_type = state.get("task_type", "classification")
            best_model_name = state.get("selected_final_model", "Selected Model")
            num_cols = state.get("numerical_columns", [])
            cat_cols = state.get("categorical_columns", [])

            trained_models = state.get("trained_models", [])
            best_model_info = next((m for m in trained_models if m.get("model_name") == best_model_name), {})
            cv_scores = best_model_info.get("cv_scores", [])
            test_metrics = best_model_info.get("test_metrics", {})

            # 1. Serialize Model Pipeline
            from app.tools.model_trainer import _pipeline_cache
            pipeline = _pipeline_cache.get(session_id) or _pipeline_cache.get("default")
            model_path = None
            if pipeline is not None:
                model_path = packager.serialize_model(pipeline)

            # 2. Generate Metadata
            meta_path = packager.generate_metadata(
                target_col=target_col,
                task_type=task_type,
                model_name=best_model_name,
                num_cols=num_cols,
                cat_cols=cat_cols,
                cv_scores=cv_scores,
                test_metrics=test_metrics,
                dataset_path=state.get("dataset_path_original"),
            )

            # 3. Generate Scripts
            inference_path = packager.generate_inference_script(
                target_col=target_col,
                task_type=task_type,
                is_classification=(task_type == "classification"),
            )
            packager.generate_preprocessing_script(num_cols=num_cols, cat_cols=cat_cols)
            packager.generate_training_script(target_col=target_col, task_type=task_type, model_name=best_model_name)
            packager.generate_readme(
                target_col=target_col,
                task_type=task_type,
                best_model=best_model_name,
                metrics=test_metrics,
            )

            # 4. Create Downloadable ZIP Archive
            bundle_zip = packager.create_zip_bundle()

            return {
                **state,
                "final_pipeline_path": model_path,
                "model_metadata_path": meta_path,
                "project_bundle_path": bundle_zip,
                "completed_stages": [*state.get("completed_stages", []), "ARTIFACT_PACKAGING"],
            }

        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Artifact packaging failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "ARTIFACT_PACKAGING", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        zip_path = state.get("project_bundle_path")
        return f"Production Bundle: {zip_path}" if zip_path else "Bundle packaging pending."
