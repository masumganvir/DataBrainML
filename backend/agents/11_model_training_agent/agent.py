"""
DataWise AI — Agent 11: Model Training Agent Implementation
"""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.pipeline import Pipeline

from .schemas import AgentInput, AgentOutput
from tools.preprocessing import build_column_transformer, split_dataset
from tools.models import get_candidate_models
from tools.evaluation import run_cross_validation


class ModelTrainerAgent:
    """Agent 11: Trains candidate ML models inside reproducible pipelines."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Model Training Agent"

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

                # 1. Leakage-free train/test split
                X_train, X_test, y_train, y_test = split_dataset(
                    df,
                    target_column=target,
                    test_size=0.2,
                    stratify=(task == "classification"),
                )

                num_cols = list(X_train.select_dtypes(include=[np.number]).columns)
                cat_cols = list(X_train.select_dtypes(exclude=[np.number]).columns)

                # Preprocessing blueprint
                preprocessor = build_column_transformer(num_cols, cat_cols)

                # Fetch candidate models
                candidates = get_candidate_models(task_type=task, n_samples=len(X_train), n_features=len(X_train.columns))

                # Train up to 3 candidates for fast execution
                results: List[Dict[str, Any]] = []
                scoring = "f1_weighted" if task == "classification" else "r2"

                for name, model in list(candidates.items())[:3]:
                    t0 = time.time()
                    pipe = Pipeline([("prep", preprocessor), ("model", model)])

                    # Cross validation on X_train only
                    cv_res = run_cross_validation(
                        pipe,
                        X_train,
                        y_train,
                        cv=3,
                        scoring=scoring,
                        stratified=(task == "classification"),
                    )

                    # Fit full training set
                    pipe.fit(X_train, y_train)
                    train_score = float(pipe.score(X_train, y_train))
                    test_score = float(pipe.score(X_test, y_test))
                    duration = round(time.time() - t0, 3)

                    results.append({
                        "model_name": name,
                        "cv_score_mean": cv_res["mean_score"],
                        "cv_score_std": cv_res["std_score"],
                        "train_score": round(train_score, 4),
                        "test_score": round(test_score, 4),
                        "overfitting_gap": round(train_score - test_score, 4),
                        "training_time_seconds": duration,
                    })

                # Sort by CV score
                results.sort(key=lambda x: x["cv_score_mean"], reverse=True)
                champion = results[0]["model_name"] if results else "None"

                summary = (
                    f"Model Training complete: Evaluated {len(results)} algorithms. "
                    f"Top candidate: {champion} (CV {scoring}: {results[0]['cv_score_mean']:.4f})."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "trained_models": results,
                        "champion_candidate": champion,
                        "scoring_metric": scoring,
                        "total_models_trained": len(results),
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "model_trainer", "status": "ready"},
                summary="Model Training Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Model Training Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Model Training Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
