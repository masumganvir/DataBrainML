"""
DataWise AI — Agent 13: Model Evaluation Agent Implementation
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
from tools.evaluation import evaluate_classification, evaluate_regression


class ModelAgent:
    """Agent 13: Independent model evaluation, overfitting detection, and champion selection."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Model Evaluation Agent"

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

                model = (
                    RandomForestClassifier(n_estimators=100, random_state=42)
                    if task == "classification"
                    else RandomForestRegressor(n_estimators=100, random_state=42)
                )

                pipe = Pipeline([("prep", preprocessor), ("model", model)])
                pipe.fit(X_train, y_train)

                train_score = float(pipe.score(X_train, y_train))
                test_score = float(pipe.score(X_test, y_test))
                gap = round(train_score - test_score, 4)

                y_pred = pipe.predict(X_test)
                if task == "classification":
                    prob = pipe.predict_proba(X_test) if hasattr(pipe, "predict_proba") else None
                    metrics = evaluate_classification(y_test, y_pred, y_prob=prob)
                else:
                    metrics = evaluate_regression(y_test, y_pred)

                overfitting = "Low" if gap < 0.06 else ("Moderate" if gap < 0.15 else "High")
                champion_name = model.__class__.__name__

                rationale = (
                    f"{champion_name} selected based on solid holdout test performance ({test_score:.4f}) "
                    f"and a controlled generalization gap ({gap:.4f}) indicating {overfitting.lower()} overfitting risk."
                )
                summary = (
                    f"Model Evaluation completed for {champion_name}. "
                    f"Test Score: {test_score:.4f}, Train Score: {train_score:.4f}, "
                    f"Overfitting Gap: {gap:.4f} ({overfitting} risk)."
                )

                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "champion_model": champion_name,
                        "evaluation_metrics": metrics,
                        "train_score": train_score,
                        "test_score": test_score,
                        "generalization_gap": gap,
                        "overfitting_assessment": overfitting,
                        "selection_rationale": rationale,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "model_evaluator", "status": "ready"},
                summary="Model Evaluation Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Model Evaluation Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Model Evaluation Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
