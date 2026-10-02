"""
DataWise AI — Training Agent
Specialized agent for leak-free model training, cross-validation, and performance evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.model_trainer import ModelTrainer
from app.tools.target_detector import TargetDetector


class TrainingAgent(BaseAgent):
    """
    Orchestrates leak-free model training, cross-validation, and test evaluation.
    """

    def __init__(self) -> None:
        super().__init__(
            name="TrainingAgent",
            role="AutoML Training & Cross-Validation Specialist",
            description="Executes train/test split, builds leak-free ColumnTransformer pipelines, performs K-Fold/Stratified cross-validation, and ranks candidate models.",
            system_prompt=(
                "You are an expert AutoML training engineer. "
                "Ensure strict data leakage prevention by fitting all scalers and encoders only on training data. "
                "Select task-appropriate evaluation metrics (e.g. PR-AUC for imbalanced data, RMSE for regression). "
                "Explain model comparison trade-offs between linear, tree-based, and boosting architectures."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Initiating model training workflow for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        target_col = state.get("target_column")
        task_type = state.get("task_type")

        # Auto-detect target if not explicitly defined
        if not target_col:
            detected = TargetDetector(df).detect()
            target_col = detected.get("recommended_target")
            task_type = detected.get("recommended_task", "classification")
            if target_col:
                logger.info(f"[{self.name}] Inferred target column '{target_col}' ({task_type})")
            else:
                logger.warning(f"[{self.name}] No target column found; cannot train supervised models.")
                return {
                    **state,
                    "errors": [*state.get("errors", []), {"stage": "TRAINING", "error": "Target column is required for model training."}],
                }

        try:
            trainer = ModelTrainer(
                df=df,
                target_col=target_col,
                task_type=task_type,
                primary_metric=state.get("primary_metric"),
                cv_folds=state.get("cv_folds", 5),
            )
            results = trainer.train_and_evaluate()

            # Store fitted pipeline in module cache for downstream serialization & inference scripts
            best_pipeline = results["best_pipeline"]
            from app.tools.model_trainer import _pipeline_cache  # type: ignore
            _pipeline_cache[state.get("session_id", "default")] = best_pipeline

            return {
                **state,
                "target_column": target_col,
                "task_type": results["task_type"],
                "primary_metric": results["primary_metric"],
                "cv_strategy": results["cv_strategy"],
                "trained_models": results["trained_models"],
                "selected_final_model": results["best_model_name"],
                "current_stage": "EVALUATION",
                "completed_stages": [*state.get("completed_stages", []), "TRAINING"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Model training failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "TRAINING", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        models = state.get("trained_models", [])
        if not models:
            return "No models trained yet."

        metric = state.get("primary_metric", "Score")
        lines = [f"Trained Models ({state.get('cv_strategy', 'Cross-Validation')}) under {metric}:"]
        for m in models:
            sel = " [SELECTED]" if m.get("is_selected") else ""
            lines.append(
                f"- {m['model_name']}: CV {metric}={m['cv_mean']} ± {m['cv_std']} | "
                f"Test {metric}={m['test_metrics'].get(metric, 'N/A')} | "
                f"Time={m['training_time_seconds']}s{sel}"
            )
        lines.append(f"Selected Candidate: {state.get('selected_final_model', 'None')}")
        return "\n".join(lines)
