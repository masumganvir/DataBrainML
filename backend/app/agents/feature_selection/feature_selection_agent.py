"""
DataWise AI — Feature Selection Agent
Specialized agent for dimensional reduction, relevance ranking, and noise elimination.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.feature_selection import FeatureSelector


class FeatureSelectionAgent(BaseAgent):
    """Prunes low-variance, collinear, or uninformative features to prevent overfitting and curse of dimensionality."""

    def __init__(self) -> None:
        super().__init__(
            name="FeatureSelectionAgent",
            role="Feature Selection & Dimensionality Specialist",
            description="Applies variance thresholding, correlation pruning, mutual information, and tree feature importance.",
            system_prompt=(
                "You are an expert in feature selection and dimensionality reduction. "
                "Help the user choose between filter methods (mutual information, correlation), "
                "wrapper methods (recursive feature elimination), and embedded methods (L1/Lasso, tree importances). "
                "Prevent overfitting, collinear redundancy, and improve model interpretability."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Running feature selection for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        try:
            selector = FeatureSelector(
                df,
                target_column=state.get("target_column"),
                task_type=state.get("task_type"),
            )
            result = selector.run_all()
            return {
                **state,
                "feature_selection_results": result.get("feature_details", []),
                "selected_features": result.get("selected_features", []),
                "current_stage": "TARGET_DETECTION",
                "completed_stages": [*state.get("completed_stages", []), "FEATURE_SELECTION"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Feature selection failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "FEATURE_SELECTION", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        selected = state.get("selected_features", [])
        return f"Selected Features Count: {len(selected)}: {selected[:8]}"
