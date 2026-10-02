"""
DataWise AI — ML Problem Detection Agent
Determines problem type (Binary Classification, Multiclass Classification,
Regression, Clustering, Anomaly Detection, Time-Series Forecasting)
based on target characteristics, dataset dimensions, and temporal ordering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class ProblemTypeAgent(BaseAgent):
    """Problem Type Detection & Target Analyzer Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Problem Type Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Problem detection failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        user_objective = input_data.parameters.get("objective", "").lower()

        # If user explicitly states clustering or anomaly detection without target:
        if not target_col or target_col not in df.columns:
            if "anomaly" in user_objective or "fraud" in user_objective or "outlier" in user_objective:
                problem_type = "anomaly_detection"
                rationale = "No target column designated; objective specifies anomaly or outlier detection."
            elif "cluster" in user_objective or "segment" in user_objective:
                problem_type = "clustering"
                rationale = "No target column designated; objective specifies customer or record clustering."
            else:
                # Default candidate: inspect last column as possible target or clustering
                last_col = df.columns[-1]
                n_uniq = df[last_col].nunique()
                if n_uniq <= 20:
                    problem_type = "classification"
                    target_col = last_col
                    rationale = f"Inferring last column '{last_col}' ({n_uniq} unique values) as classification target."
                else:
                    problem_type = "clustering"
                    rationale = "No low-cardinality target detected; default unsupervised clustering configured."

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "problem_type": problem_type,
                    "target_column": target_col,
                    "rationale": rationale,
                },
                summary=f"Detected ML Problem Type: {problem_type.upper()}. {rationale}",
            )

        # Analyze target column
        s = df[target_col].dropna()
        n_unique = s.nunique()
        is_numeric = pd.api.types.is_numeric_dtype(s)

        # Check for time-series characteristics
        has_datetime = any(pd.api.types.is_datetime64_any_dtype(df[c]) or "date" in c.lower() for c in df.columns)

        if "forecast" in user_objective or (has_datetime and is_numeric and n_unique > 20 and "time" in user_objective):
            problem_type = "time_series"
            sub_type = "time_series_forecasting"
            primary_metric = "RMSE"
            rationale = f"Datetime ordering with continuous target '{target_col}' indicates time-series forecasting."
        elif n_unique == 2:
            problem_type = "classification"
            sub_type = "binary_classification"
            # Check class balance
            ratio = s.value_counts(normalize=True).iloc[1]
            primary_metric = "F1" if (ratio < 0.2 or ratio > 0.8) else "ROC_AUC"
            rationale = f"Target '{target_col}' has exactly 2 classes (positive ratio: {ratio:.1%}). Configured Binary Classification."
        elif n_unique <= 20 and (not is_numeric or n_unique < len(s) * 0.05):
            problem_type = "classification"
            sub_type = "multiclass_classification"
            primary_metric = "Balanced_Accuracy"
            rationale = f"Target '{target_col}' has {n_unique} discrete categories. Configured Multiclass Classification."
        else:
            problem_type = "regression"
            sub_type = "continuous_regression"
            primary_metric = "R2"
            rationale = f"Target '{target_col}' is a continuous numeric variable with {n_unique} unique values. Configured Regression."

        summary = f"Detected ML Problem: {sub_type.upper().replace('_', ' ')} for target '{target_col}' (Primary Metric: {primary_metric})."

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "problem_type": problem_type,
                "sub_type": sub_type,
                "target_column": target_col,
                "target_unique_values": n_unique,
                "primary_metric": primary_metric,
                "rationale": rationale,
            },
            summary=summary,
        )
