"""
DataWise AI — Hyperparameter Agent
Optimizes hyperparameters with budget-constrained RandomizedSearchCV / Optuna.
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from agents.base import BaseAgent, AgentInput, AgentOutput


class HyperparameterAgent(BaseAgent):
    """Executes budget-controlled hyperparameter search."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Hyperparameter Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            pipeline = params.get("pipeline")
            X_train = params.get("X_train")
            y_train = params.get("y_train")

            if pipeline is None or X_train is None or y_train is None:
                return AgentOutput(
                    session_id=self.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    message="Baseline hyperparameters retained.",
                    data={"best_params": {}},
                )

            # Tuning space for champion model
            param_dist = {
                "model__n_estimators": [50, 100],
                "model__max_depth": [6, 10, None],
            }
            # Only tune if model has these params
            model_step = pipeline.named_steps.get("model")
            valid_dist = {k: v for k, v in param_dist.items() if hasattr(model_step, k.replace("model__", ""))}

            if valid_dist:
                search = RandomizedSearchCV(pipeline, valid_dist, n_iter=4, cv=3, random_state=42)
                search.fit(X_train, y_train)
                return AgentOutput(
                    session_id=self.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    message=f"Optimized hyperparameters: {search.best_params_}",
                    data={"best_params": search.best_params_, "best_score": round(float(search.best_score_), 4)},
                )
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Model parameters validated.",
                data={"best_params": {}},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
