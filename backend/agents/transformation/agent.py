"""
DataWise AI — Feature Transformation Agent
Detects distribution skewness, heavy tails, and applies power transforms
(log1p, Yeo-Johnson, Box-Cox, QuantileTransformer).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class TransformationAgent(BaseAgent):
    """Distribution Transformation & Non-Linear Mapping Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Transformation Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Transformation analysis failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
        transformation_plans: List[Dict[str, Any]] = []

        for col in num_cols:
            s = df[col].dropna()
            if len(s) < 20 or s.nunique() <= 2:
                continue

            skew = float(stats.skew(s))
            kurt = float(stats.kurtosis(s))
            min_val = float(s.min())

            # Evaluate need for transformation
            if abs(skew) > 1.2 or kurt > 3.0:
                if min_val >= 0 and skew > 1.2:
                    transformer = "log1p"
                    rationale = f"Severe positive skewness (skew={skew:.2f}). log1p compresses right tail."
                elif min_val > 0:
                    transformer = "PowerTransformer(method='box-cox')"
                    rationale = f"Strictly positive skewed data (skew={skew:.2f}). Box-Cox maximizes normality."
                else:
                    transformer = "PowerTransformer(method='yeo-johnson')"
                    rationale = f"Skewed distribution with zero/negative values (min={min_val}, skew={skew:.2f}). Yeo-Johnson supports all reals."

                transformation_plans.append({
                    "column": col,
                    "skewness": round(skew, 2),
                    "kurtosis": round(kurt, 2),
                    "recommended_transformation": transformer,
                    "rationale": rationale,
                })

        summary = (
            f"Analyzed {len(num_cols)} numerical features for distribution skewness. "
            f"Recommended power/log transformations for {len(transformation_plans)} skewed features."
            if transformation_plans else "All numerical features exhibit acceptable symmetry. No heavy transformations required."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"transformation_plan": transformation_plans},
            summary=summary,
        )
