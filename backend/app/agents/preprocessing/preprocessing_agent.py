"""
DataWise AI — Preprocessing Agent & Sub-Agents
Specialized agents for data transformation, imputation, categorical encoding, and feature scaling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.encoding import recommend_categorical_encoding
from app.tools.scaling import recommend_numerical_scaling
from app.tools.transformation import recommend_transformations


class PreprocessingAgent(BaseAgent):
    """Orchestrates comprehensive data preprocessing plans across imputation, encoding, and scaling."""

    def __init__(self) -> None:
        super().__init__(
            name="PreprocessingAgent",
            role="Data Preprocessing & Transformation Architect",
            description="Designs optimal data cleaning, imputation, categorical encoding, and feature scaling pipelines.",
            system_prompt=(
                "You are an expert in Scikit-Learn data preprocessing. "
                "Recommend the right encoder (OneHotEncoder for low cardinality, TargetEncoder or Ordinal for high cardinality), "
                "the right scaler (StandardScaler for normal distributions, RobustScaler for data with outliers, MinMaxScaler for bounded domains), "
                "and transformations (Log1p, Yeo-Johnson) to stabilize variance."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Formulating preprocessing plans for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        encoding_plan: List[Dict[str, Any]] = []
        scaling_plan: List[Dict[str, Any]] = []
        transformation_plan: List[Dict[str, Any]] = []

        try:
            encoding_plan = recommend_categorical_encoding(df)
            scaling_plan = recommend_numerical_scaling(df)
            transformation_plan = recommend_transformations(df)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{self.name}] Preprocessing recommendation warning: {exc}")

        return {
            **state,
            "encoding_plan": encoding_plan,
            "scaling_plan": scaling_plan,
            "transformation_plan": transformation_plan,
        }


class MissingValueAgent(BaseAgent):
    """Sub-agent specializing in missing value imputation strategies."""

    def __init__(self) -> None:
        super().__init__(
            name="MissingValueAgent",
            role="Missing Value Imputation Specialist",
            description="Recommends univariate and multivariate imputation techniques (mean, median, mode, KNN, IterativeImputer).",
            system_prompt="Focus exclusively on missing value diagnosis, missingness mechanisms (MCAR/MAR/MNAR), and imputation algorithms.",
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        return state


class EncodingAgent(BaseAgent):
    """Sub-agent specializing in categorical feature encoding."""

    def __init__(self) -> None:
        super().__init__(
            name="EncodingAgent",
            role="Categorical Encoding Specialist",
            description="Determines whether to use OneHot, Ordinal, Target, Weight of Evidence, or Binary encoding.",
            system_prompt="Focus on categorical cardinality, rare category handling, and preventing target leakage during encoding.",
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        return state


class ScalingAgent(BaseAgent):
    """Sub-agent specializing in feature scaling and normalization."""

    def __init__(self) -> None:
        super().__init__(
            name="ScalingAgent",
            role="Feature Scaling Specialist",
            description="Evaluates whether StandardScaler, RobustScaler, MinMaxScaler, or MaxAbsScaler is best suited.",
            system_prompt="Focus on distance-based vs gradient-based vs tree-based algorithm sensitivity to feature scales.",
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        return state


class TransformationAgent(BaseAgent):
    """Sub-agent specializing in mathematical variance stabilizing transformations."""

    def __init__(self) -> None:
        super().__init__(
            name="TransformationAgent",
            role="Power & Distribution Transformation Specialist",
            description="Recommends Log, Sqrt, Box-Cox, and Yeo-Johnson transformations to minimize skewness.",
            system_prompt="Focus on power transforms, handling zero and negative values, and improving normality.",
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        return state
