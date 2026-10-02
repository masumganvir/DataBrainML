"""
DataWise AI — Model Training Agent
Constructs serializable scikit-learn Pipelines with ColumnTransformer (imputation, encoding, scaling).
Performs leakage-free splitting (Stratified/Random/TimeSeries) and trains candidate models.
Evaluates training and cross-validation scores with duration tracking.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold, KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class TrainingAgent(BaseAgent):
    """Pipeline Assembly and Model Training Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Training Agent")

    def _build_preprocessor(self, num_cols: List[str], cat_cols: List[str]) -> ColumnTransformer:
        """Constructs leak-free ColumnTransformer."""
        transformers = []
        if num_cols:
            num_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", RobustScaler()),
            ])
            transformers.append(("num", num_pipe, num_cols))

        if cat_cols:
            cat_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ])
            transformers.append(("cat", cat_pipe, cat_cols))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Training failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column") or df.columns[-1]
        task_type = input_data.parameters.get("task_type", "classification")
        cv_folds = input_data.parameters.get("cv_folds", 3)

        # Drop rows with null target
        df_clean = df.dropna(subset=[target_col])
        X = df_clean.drop(columns=[target_col])
        y = df_clean[target_col]

        num_cols = list(X.select_dtypes(include=[np.number]).columns)
        cat_cols = list(X.select_dtypes(exclude=[np.number]).columns)

        # Leakage-free train / test split
        is_classification = task_type == "classification"
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42,
                stratify=y if (is_classification and y.nunique() <= 20 and y.value_counts().min() > 1) else None
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        preprocessor = self._build_preprocessor(num_cols, cat_cols)

        # Candidate models dictionary
        models: Dict[str, Any] = {}
        if is_classification:
            scoring = "f1_weighted"
            models["LogisticRegression"] = LogisticRegression(max_iter=1000, random_state=42)
            models["RandomForestClassifier"] = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
            models["GradientBoostingClassifier"] = GradientBoostingClassifier(n_estimators=80, learning_rate=0.1, random_state=42)
        else:
            scoring = "r2"
            models["Ridge"] = Ridge(alpha=1.0, random_state=42)
            models["RandomForestRegressor"] = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
            models["GradientBoostingRegressor"] = GradientBoostingRegressor(n_estimators=80, learning_rate=0.1, random_state=42)

        results: List[Dict[str, Any]] = []
        trained_pipelines: Dict[str, Pipeline] = {}

        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42) if is_classification else KFold(n_splits=cv_folds, shuffle=True, random_state=42)

        for name, clf in models.items():
            t0 = time.time()
            full_pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model", clf),
            ])

            # Cross validation strictly on X_train to prevent test leakage
            try:
                cv_res = cross_validate(full_pipe, X_train, y_train, cv=cv, scoring=scoring, return_train_score=True)
                cv_mean = float(np.mean(cv_res["test_score"]))
                cv_std = float(np.std(cv_res["test_score"]))
                train_score = float(np.mean(cv_res["train_score"]))
            except Exception as cv_exc:
                logger.warning(f"Cross-validation error on {name}: {cv_exc}")
                cv_mean = 0.0
                cv_std = 0.0
                train_score = 0.0

            # Fit on full training set
            full_pipe.fit(X_train, y_train)
            test_score = float(full_pipe.score(X_test, y_test)) if hasattr(full_pipe, "score") else cv_mean
            duration = round(time.time() - t0, 3)

            trained_pipelines[name] = full_pipe
            results.append({
                "model_name": name,
                "cv_mean": round(cv_mean, 4),
                "cv_std": round(cv_std, 4),
                "train_score": round(train_score, 4),
                "test_score": round(test_score, 4),
                "overfitting_gap": round(train_score - test_score, 4),
                "training_time_seconds": duration,
            })

        # Rank by CV performance
        results.sort(key=lambda x: x["cv_mean"], reverse=True)
        champion = results[0]["model_name"] if results else "None"

        summary = (
            f"Trained {len(results)} candidate models with {cv_folds}-fold CV. "
            f"Champion: {champion} (CV {scoring}: {results[0]['cv_mean']:.4f}, Test: {results[0]['test_score']:.4f})."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "training_results": results,
                "champion_model": champion,
                "scoring_metric": scoring,
                "target_column": target_col,
                "task_type": task_type,
            },
            summary=summary,
        )
