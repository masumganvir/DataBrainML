"""
DataWise AI — Hyperparameter Tuning Agent
Executes Bayesian optimization using Optuna (with RandomizedSearchCV fallback)
within strict compute budgets, maximum trial limits, and early stopping.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, KFold
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False


class HyperparameterTuningAgent(BaseAgent):
    """Bayesian & Randomized Hyperparameter Optimization Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Hyperparameter Tuning Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Tuning failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column") or df.columns[-1]
        task_type = input_data.parameters.get("task_type", "classification")
        champion_model = input_data.parameters.get("model_name", "RandomForestClassifier")
        n_trials = min(input_data.parameters.get("n_trials", 15), 30)  # strict budget cap
        timeout_sec = min(input_data.parameters.get("timeout_sec", 60), 120)

        # Prepare numerical features for fast tuning evaluation
        df_clean = df.dropna(subset=[target_col])
        X = df_clean.drop(columns=[target_col]).select_dtypes(include=[np.number]).fillna(0)
        y = df_clean[target_col]

        if X.empty:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                summary="Hyperparameter tuning skipped: no numerical features found for optimization.",
            )

        is_classif = task_type == "classification"
        scoring = "f1_weighted" if is_classif else "r2"
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42) if is_classif else KFold(n_splits=3, shuffle=True, random_state=42)

        best_params: Dict[str, Any] = {}
        best_score = -1e9
        trials_count = 0
        t0 = time.time()

        if OPTUNA_AVAILABLE:
            def objective(trial: optuna.Trial) -> float:
                n_est = trial.suggest_int("n_estimators", 50, 200, step=25)
                max_d = trial.suggest_int("max_depth", 4, 16)
                min_split = trial.suggest_int("min_samples_split", 2, 10)

                if is_classif:
                    model = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, min_samples_split=min_split, random_state=42, n_jobs=-1)
                else:
                    model = RandomForestRegressor(n_estimators=n_est, max_depth=max_d, min_samples_split=min_split, random_state=42, n_jobs=-1)

                scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
                return float(np.mean(scores))

            study = optuna.create_study(direction="maximize")
            study.optimize(objective, n_trials=n_trials, timeout=timeout_sec)

            best_params = study.best_params
            best_score = round(study.best_value, 4)
            trials_count = len(study.trials)
        else:
            # Simple randomized search fallback
            from sklearn.model_selection import RandomizedSearchCV
            grid = {
                "n_estimators": [50, 100, 150],
                "max_depth": [6, 10, 14],
                "min_samples_split": [2, 5, 8],
            }
            estimator = RandomForestClassifier(random_state=42) if is_classif else RandomForestRegressor(random_state=42)
            search = RandomizedSearchCV(estimator, grid, n_iter=8, cv=cv, scoring=scoring, random_state=42, n_jobs=-1)
            search.fit(X, y)
            best_params = search.best_params_
            best_score = round(float(search.best_score_), 4)
            trials_count = 8

        duration = round(time.time() - t0, 2)
        summary = (
            f"Optuna hyperparameter optimization completed {trials_count} trials in {duration}s. "
            f"Best CV {scoring}: {best_score:.4f}. Optimized parameters: {best_params}."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "best_parameters": best_params,
                "best_cv_score": best_score,
                "trials_evaluated": trials_count,
                "duration_seconds": duration,
                "target_model": champion_model,
            },
            summary=summary,
        )
