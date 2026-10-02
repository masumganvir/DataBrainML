"""
DataWise AI — Model Training Agent
Executes candidate model training inside reproducible, leak-free pipelines.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.model_trainer import ModelTrainer, train_candidate_models


class ModelTrainingAgent(BaseAgent):
    """Executes candidate model training and produces the champion estimator."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Model Training Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(
                    session_id=self.session_id,
                    agent_name=self.agent_name,
                    status="error",
                    message="DataFrame required for ModelTrainingAgent",
                )

            target_col = params.get("target_column") or df.columns[-1]
            task_type = params.get("task_type", "classification")
            cv_folds = params.get("cv_folds", 5)

            results = train_candidate_models(
                df=df,
                target_col=target_col,
                task_type=task_type,
                cv_folds=cv_folds,
            )

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                data=results,
                message=f"Trained candidate models. Champion: {results['best_model_name']}",
            )
        except Exception as exc:
            logger.error(f"ModelTrainingAgent error: {exc}")
            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="error",
                message=str(exc),
            )
