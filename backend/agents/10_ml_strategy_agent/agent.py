"""
DataWise AI — Agent 10: ML Strategy Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.models import get_candidate_models


class MLStrategyAgent:
    """Agent 10: Formulates task strategy, candidate models, and primary evaluation metric."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "ML Strategy Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                path = input_data.dataset_path
                ext = Path(path).suffix.lower()
                if ext in (".xlsx", ".xls"):
                    df = pd.read_excel(path)
                elif ext == ".json":
                    df = pd.read_json(path)
                else:
                    df = pd.read_csv(path, low_memory=False)

                target = input_data.parameters.get("target_column")
                if not target or target not in df.columns:
                    target = df.columns[-1]

                target_series = df[target]
                unique_cnt = target_series.nunique(dropna=True)
                is_numeric = pd.api.types.is_numeric_dtype(target_series)

                # Determine task
                if is_numeric and unique_cnt > 30 and (unique_cnt / len(df)) > 0.05:
                    task = "regression"
                    primary_metric = "RMSE"
                else:
                    task = "classification"
                    # Imbalance check
                    vc = target_series.value_counts(normalize=True)
                    if len(vc) > 1 and vc.iloc[0] > 0.70:
                        primary_metric = "F1-Weighted"
                    else:
                        primary_metric = "Accuracy"

                candidates_dict = get_candidate_models(
                    task_type=task,
                    n_samples=len(df),
                    n_features=len(df.columns),
                )
                candidate_names = list(candidates_dict.keys())

                summary = (
                    f"ML Strategy formulated: Task='{task}' targeting '{target}'. "
                    f"Primary metric='{primary_metric}'. "
                    f"Shortlisted {len(candidate_names)} candidate algorithms: {', '.join(candidate_names[:4])}."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "task_type": task,
                        "target_column": target,
                        "primary_metric": primary_metric,
                        "candidate_models": candidate_names,
                        "cv_folds": 5,
                        "sample_count": len(df),
                        "feature_count": len(df.columns) - 1,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "get_candidate_models", "status": "ready"},
                summary="ML Strategy Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in ML Strategy Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"ML Strategy Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
