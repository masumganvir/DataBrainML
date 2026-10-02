"""
DataWise AI — Missing Value Agent
Analyzes missingness patterns, determines optimal imputation strategy
(Mean, Median, Mode, Constant, KNNImputer, IterativeImputer, ForwardFill),
and creates sklearn-compatible imputation plans.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class MissingValuesAgent(BaseAgent):
    """Missing Value Strategy and Imputation Planning Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Missing Values Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Missing values analysis failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        n_rows = len(df)
        missing_plans: List[Dict[str, Any]] = []

        for col in df.columns:
            m_count = int(df[col].isna().sum())
            if m_count == 0:
                continue

            m_pct = round((m_count / n_rows) * 100, 2)
            series = df[col].dropna()
            is_numeric = pd.api.types.is_numeric_dtype(df[col])

            # Select strategy based on characteristics
            if m_pct > 65.0:
                strategy = "DROP_COLUMN"
                rationale = f"Over 65% missing ({m_pct}%). Imputation introduces excessive artificial variance."
            elif is_numeric:
                # Check skewness
                skewness = float(stats.skew(series)) if len(series) > 5 else 0.0
                if m_pct > 20.0 and n_rows <= 10000:
                    strategy = "KNNImputer"
                    rationale = f"Moderate missingness ({m_pct}%) in tabular numerical data. KNN captures multivariate relations."
                elif abs(skewness) > 1.0:
                    strategy = "median"
                    rationale = f"Right/left skewed distribution (skew={skewness:.2f}). Median is resistant to extreme values."
                else:
                    strategy = "mean"
                    rationale = f"Approximately normal distribution (skew={skewness:.2f}). Mean minimizes reconstruction variance."
            else:
                # Categorical
                if m_pct < 5.0:
                    strategy = "most_frequent"
                    rationale = f"Low missing percentage ({m_pct}%). Mode preserves existing categorical frequency."
                else:
                    strategy = "constant"
                    rationale = f"Notable categorical missingness ({m_pct}%). Introducing 'Missing' category retains missingness signal."

            missing_plans.append({
                "column": col,
                "missing_count": m_count,
                "missing_pct": m_pct,
                "is_numeric": is_numeric,
                "recommended_strategy": strategy,
                "alternative_strategies": ["KNNImputer", "median", "mean", "most_frequent", "constant", "DROP_COLUMN"],
                "rationale": rationale,
            })

        summary = (
            f"Detected missing values in {len(missing_plans)} columns. "
            f"Formulated imputation plan utilizing median, mode, constant, and KNN strategies."
            if missing_plans else "No missing values detected across all columns. Dataset is complete."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "missing_value_plan": missing_plans,
                "columns_with_missing": len(missing_plans),
            },
            summary=summary,
        )
