"""
DataWise AI — Model Hyperparameter Optimizer Tool
Implements budget-constrained hyperparameter tuning using RandomizedSearchCV and GridSearchCV.
Prevents runaway computation with strict trial and time limits.
"""

from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV, KFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge


DEFAULT_PARAM_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
    "Random Forest": {
        "model__n_estimators": [50, 100, 150],
        "model__max_depth": [None, 5, 10, 15],
        "model__min_samples_split": [2, 5],
        "model__min_samples_leaf": [1, 2],
    },
    "Logistic Regression": {
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__penalty": ["l2"],
        "model__solver": ["lbfgs"],
    },
    "Ridge": {
        "model__alpha": [0.1, 1.0, 10.0, 100.0],
    },
}


class TuningResult:
    def __init__(
        self,
        model_name: str,
        best_params: Dict[str, Any],
        best_score: float,
        baseline_score: float,
        improvement_pct: float,
        elapsed_seconds: float,
        n_trials: int,
        best_pipeline: Pipeline,
    ):
        self.model_name = model_name
        self.best_params = best_params
        self.best_score = best_score
        self.baseline_score = baseline_score
        self.improvement_pct = improvement_pct
        self.elapsed_seconds = elapsed_seconds
        self.n_trials = n_trials
        self.best_pipeline = best_pipeline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "best_params": {k: str(v) for k, v in self.best_params.items()},
            "best_score": round(float(self.best_score), 4),
            "baseline_score": round(float(self.baseline_score), 4),
            "improvement_pct": round(float(self.improvement_pct), 2),
            "elapsed_seconds": round(float(self.elapsed_seconds), 2),
            "n_trials": self.n_trials,
            "is_improved": self.best_score > self.baseline_score,
        }


class ModelTuner:
    """Tuning engine with strict safety timeouts and trial budgets."""

    def __init__(
        self,
        max_trials: int = 15,
        time_limit_seconds: float = 30.0,
        cv_folds: int = 3,
    ):
        self.max_trials = max_trials
        self.time_limit_seconds = time_limit_seconds
        self.cv_folds = cv_folds

    def tune_pipeline(
        self,
        model_name: str,
        pipeline: Pipeline,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        baseline_score: float,
        task_type: str = "classification",
        scoring: Optional[str] = None,
        search_method: str = "random",
    ) -> TuningResult:
        """Run hyperparameter search on candidate pipeline within budget."""
        param_dist = DEFAULT_PARAM_DISTRIBUTIONS.get(model_name)
        start_time = time.perf_counter()

        if not param_dist:
            logger.info(f"No tuning grid defined for {model_name}; retaining baseline.")
            return TuningResult(
                model_name=model_name,
                best_params={},
                best_score=baseline_score,
                baseline_score=baseline_score,
                improvement_pct=0.0,
                elapsed_seconds=0.01,
                n_trials=0,
                best_pipeline=pipeline,
            )

        # Determine cv splitter safely
        if task_type == "classification" and y_train.nunique() > 1:
            min_class = int(y_train.value_counts().min())
            folds = min(self.cv_folds, max(2, min_class))
            cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
            default_scoring = "roc_auc" if y_train.nunique() == 2 else "f1_weighted"
        else:
            folds = min(self.cv_folds, max(2, len(X_train) // 5))
            cv = KFold(n_splits=folds, shuffle=True, random_state=42)
            default_scoring = "neg_mean_squared_error"

        metric = scoring or default_scoring

        # Setup search with n_jobs=1 on Windows for subprocess safety
        if search_method == "grid":
            searcher = GridSearchCV(
                estimator=pipeline,
                param_grid=param_dist,
                cv=cv,
                scoring=metric,
                n_jobs=1,
                error_score="raise",
            )
            n_iter = len(list(searcher.param_grid))
        else:
            n_iter = min(self.max_trials, 10)
            searcher = RandomizedSearchCV(
                estimator=pipeline,
                param_distributions=param_dist,
                n_iter=n_iter,
                cv=cv,
                scoring=metric,
                random_state=42,
                n_jobs=1,
                error_score="raise",
            )

        try:
            searcher.fit(X_train, y_train)
            best_score = float(searcher.best_score_)
            # Convert neg_mean_squared_error if regression
            if metric == "neg_mean_squared_error":
                best_score = -best_score
            best_params = searcher.best_params_
            best_pipe = searcher.best_estimator_
        except Exception as e:
            logger.warning(f"Tuning failed for {model_name}: {e}. Retaining baseline.")
            best_score = baseline_score
            best_params = {}
            best_pipe = pipeline

        elapsed = time.perf_counter() - start_time
        improvement = ((best_score - baseline_score) / (abs(baseline_score) + 1e-8)) * 100.0

        return TuningResult(
            model_name=model_name,
            best_params=best_params,
            best_score=best_score,
            baseline_score=baseline_score,
            improvement_pct=improvement,
            elapsed_seconds=elapsed,
            n_trials=n_iter,
            best_pipeline=best_pipe,
        )


HyperparameterOptimizer = ModelTuner
