"""
DataWise AI — Task Detection Agent
Statistically detects whether the problem is Classification (binary/multiclass) or Regression.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.target_detector import TargetDetector


class TaskDetectionAgent(BaseAgent):
    """Detects target variable and mathematical problem formulation."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Task Detection Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            df = params.get("df")
            if df is None and input_data.dataset_path:
                df = pd.read_csv(input_data.dataset_path)

            if df is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing dataframe")

            td = TargetDetector(df)
            detection = td.detect()

            target = params.get("target_column") or detection.get("recommended_target") or df.columns[-1]
            task_type = "Classification"
            if target in df.columns:
                n_unique = df[target].nunique()
                if n_unique > 20 and df[target].dtype in [np.float64, np.float32]:
                    task_type = "Regression"
                elif n_unique == 2:
                    task_type = "Binary Classification"
                elif n_unique > 2:
                    task_type = "Multiclass Classification"

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Detected task: {task_type} for target '{target}'",
                data={"target_column": target, "task_type": task_type, "detection_meta": detection},
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
