"""
DataWise AI — Feature Scaling Agent
Determines optimal scaling method (StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler)
based on distribution, presence of outliers, and target algorithm sensitivity.
Prevents unnecessary scaling when using tree-based ensembles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class ScalingAgent(BaseAgent):
    """Feature Scaling Strategy Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Scaling Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Scaling analysis failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        model_family = input_data.parameters.get("model_family", "general")
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]

        scaling_plans: List[Dict[str, Any]] = []
        is_tree_ensemble = model_family in ("tree", "random_forest", "xgboost", "lightgbm")

        for col in num_cols:
            s = df[col].dropna()
            if len(s) < 5 or s.nunique() <= 2:
                continue

            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            iqr = q3 - q1
            has_outliers = bool(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).any())
            min_val = float(s.min())
            max_val = float(s.max())

            if is_tree_ensemble:
                scaler = "Passthrough (None)"
                rationale = "Tree-based models are scale-invariant; raw feature scaling omitted to preserve split interpretability."
            elif has_outliers:
                scaler = "RobustScaler"
                rationale = "Outliers present; RobustScaler uses median and IQR to avoid distortion."
            elif min_val >= 0 and max_val <= 1:
                scaler = "Passthrough (Already [0, 1])"
                rationale = "Feature already strictly bounded in [0, 1]."
            elif min_val >= 0 and max_val <= 100 and "pct" in col.lower() or "percent" in col.lower():
                scaler = "MinMaxScaler"
                rationale = "Bounded percentage domain; MinMaxScaler scales neatly to [0, 1]."
            else:
                scaler = "StandardScaler"
                rationale = "Standard z-score normalization (zero mean, unit variance) optimal for linear and neural models."

            scaling_plans.append({
                "column": col,
                "has_outliers": has_outliers,
                "recommended_scaler": scaler,
                "rationale": rationale,
            })

        summary = (
            f"Configured feature scaling for {len(scaling_plans)} numerical features. "
            f"Target architecture: {model_family}. Applied outlier-aware scalers."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"scaling_plan": scaling_plans, "is_tree_ensemble": is_tree_ensemble},
            summary=summary,
        )
