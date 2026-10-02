"""
DataWise AI — Cross Validation Agent
Executes stratified / grouped / time-series cross-validation without leakage.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.model_trainer import ModelTrainer


class CrossValidationAgent(BaseAgent):
    """Executes robust cross-validation on the training set."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Cross Validation Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            target_col = params.get("target_column") or df.columns[-1]
            task_type = params.get("task_type", "classification")

            trainer = ModelTrainer(df=df, target_col=target_col, task_type=task_type)
            res = trainer.train_and_evaluate()

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Completed {res['cv_strategy']} cross-validation.",
                data={"cv_strategy": res["cv_strategy"], "models": res["trained_models"]},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
