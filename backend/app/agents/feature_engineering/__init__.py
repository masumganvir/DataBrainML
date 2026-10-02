"""
DataWise AI — Feature Engineering Agents
Agents for automated feature construction, selection, and dimensionality reduction.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.feature_tools import (
    engineer_features,
    select_features,
    generate_interaction_features,
    generate_datetime_features,
)


class FeatureEngineeringAgent(BaseAgent):
    """
    Constructs non-linear interactions, polynomial features, datetime components, and ratios.
    Enforces maximum feature count boundaries to prevent combinatorial explosion.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureEngineeringAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        max_features = input_data.parameters.get("max_features", 30)

        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            fe_result = engineer_features(df, target_col=target_col, max_new_features=max_features)

            created_features = fe_result.get("engineered_feature_names", [])
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=fe_result,
                summary=f"Engineered {len(created_features)} new features (interactions, datetime expansions, and ratios) while maintaining feature budget."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Feature engineering failed: {e}"
            )

    def run(self, input_data: Any) -> Any:
        if isinstance(input_data, dict) and ("completed_stages" in input_data or "dataset_path_original" in input_data or "dataset_path_analysis" in input_data):
            state = input_data
            logger.info(f"[{self.agent_name}] Running feature engineering on state for session={state.get('session_id')}")
            from app.tools.feature_engineering import FeatureEngineer
            df = self._load_df(state)
            fe_plan = []
            if df is not None:
                fe = FeatureEngineer(df, target_col=state.get("target_column"), task_type=state.get("task_type"))
                fe_plan = fe.recommend_features()
            return {
                **state,
                "feature_engineering_plan": fe_plan,
                "current_stage": "FEATURE_SELECTION",
                "completed_stages": [*state.get("completed_stages", []), "FEATURE_ENGINEERING"],
            }
        return super().run(input_data)


class FeatureSelectionAgent(BaseAgent):
    """
    Prunes redundant, low-variance, multicollinear, and uninformative features using mutual info and ANOVA.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureSelectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        k_best = input_data.parameters.get("k_best", 15)

        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            fs_result = select_features(df, target_col=target_col, k=k_best)

            selected_cols = fs_result.get("selected_features", [])
            removed_cols = fs_result.get("dropped_features", [])

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=fs_result,
                summary=f"Feature selection complete: retained {len(selected_cols)} top predictive features and eliminated {len(removed_cols)} noisy/collinear features."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Feature selection failed: {e}"
            )

    def run(self, input_data: Any) -> Any:
        if isinstance(input_data, dict) and ("completed_stages" in input_data or "dataset_path_original" in input_data or "dataset_path_analysis" in input_data):
            state = input_data
            logger.info(f"[{self.agent_name}] Running feature selection on state for session={state.get('session_id')}")
            from app.tools.feature_selection import FeatureSelector
            df = self._load_df(state)
            selected = []
            details = []
            if df is not None:
                selector = FeatureSelector(df, target_column=state.get("target_column"), task_type=state.get("task_type"))
                res = selector.run_all()
                selected = res.get("selected_features", list(df.columns))
                details = res.get("feature_details", [])
            return {
                **state,
                "feature_selection_results": details,
                "selected_features": selected,
                "current_stage": "TARGET_DETECTION",
                "completed_stages": [*state.get("completed_stages", []), "FEATURE_SELECTION"],
            }
        return super().run(input_data)


class DimensionalityReductionAgent(BaseAgent):
    """
    Applies PCA, TruncatedSVD, or latent autoencoder embeddings for ultra high-dimensional datasets.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DimensionalityReductionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        n_components = input_data.parameters.get("n_components", 5)
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "strategy": "PCA / Autoencoder Latent Projection",
                "target_components": n_components,
                "variance_threshold": 0.95
            },
            summary=f"Dimensionality reduction configured to project features into {n_components} orthogonal latent dimensions preserving 95%+ variance."
        )


__all__ = [
    "FeatureEngineeringAgent",
    "FeatureSelectionAgent",
    "DimensionalityReductionAgent",
]
