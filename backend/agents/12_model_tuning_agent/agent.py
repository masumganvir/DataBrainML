"""
DataWise AI — Agent 12: Model Tuning Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline

from .schemas import AgentInput, AgentOutput
from tools.preprocessing import build_column_transformer, split_dataset
from tools.tuning import run_random_search, MODEL_TUNING_MAX_TRIALS


class ModelAgent:
    """Agent 12: Hyperparameter optimization bounded by strict trial budgets."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Model Tuning Agent"

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
                task = input_data.parameters.get("task_type", "classification")

                if not target or target not in df.columns:
                    target = df.columns[-1]

                X_train, X_test, y_train, y_test = split_dataset(
                    df,
                    target_column=target,
                    test_size=0.2,
                    stratify=(task == "classification"),
                )

                num_cols = list(X_train.select_dtypes(include=[np.number]).columns)
                cat_cols = list(X_train.select_dtypes(exclude=[np.number]).columns)
                preprocessor = build_column_transformer(num_cols, cat_cols)

                base_model = RandomForestClassifier(random_state=42) if task == "classification" else RandomForestRegressor(random_state=42)
                pipe = Pipeline([("prep", preprocessor), ("model", base_model)])

                param_dist = {
                    "model__n_estimators": [50, 100, 150],
                    "model__max_depth": [None, 4, 8, 12],
                    "model__min_samples_split": [2, 5],
                }

                n_trials = min(input_data.parameters.get("max_trials", 6), MODEL_TUNING_MAX_TRIALS)
                scoring = "f1_weighted" if task == "classification" else "r2"

                tune_res = run_random_search(
                    estimator=pipe,
                    param_distributions=param_dist,
                    X=X_train,
                    y=y_train,
                    n_iter=n_trials,
                    cv=3,
                    scoring=scoring,
                )

                summary = (
                    f"Model Tuning completed {n_trials} trials for {base_model.__class__.__name__}. "
                    f"Best CV Score: {tune_res['best_score']:.4f} with params: {tune_res['best_params']}."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "best_params": tune_res["best_params"],
                        "best_score": tune_res["best_score"],
                        "trials_evaluated": n_trials,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "run_random_search", "status": "ready"},
                summary="Model Tuning Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Model Tuning Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Model Tuning Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
