"""
DataWise AI — ExperimentManagerAgent (Section 5 & 20)
Tracks and versions all experiments, hyperparameters, CV folds, run durations,
and model artifact checkpoints.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class ExperimentRun(BaseModel):
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    algorithm: str
    preprocessing_version: str = "v1"
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    cv_mean: float = 0.0
    cv_std: float = 0.0
    test_score: float = 0.0
    training_duration_seconds: float = 0.0
    created_at: float = Field(default_factory=time.time)


class ExperimentManagerAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ExperimentManagerAgent")
        self.runs: List[ExperimentRun] = []

    def record_run(self, run: ExperimentRun) -> None:
        self.runs.append(run)
        logger.info(f"[ExperimentManagerAgent] Logged experiment {run.experiment_id}: {run.algorithm} score={run.cv_mean:.4f}")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        p = input_data.parameters
        run = ExperimentRun(
            algorithm=p.get("algorithm", "Unknown"),
            preprocessing_version=p.get("preprocessing_version", "v1"),
            hyperparameters=p.get("hyperparameters", {}),
            cv_mean=float(p.get("cv_mean", 0.0)),
            cv_std=float(p.get("cv_std", 0.0)),
            test_score=float(p.get("test_score", 0.0)),
            training_duration_seconds=float(p.get("training_duration", 0.0)),
        )
        self.record_run(run)
        return AgentOutput(
            success=True,
            data=run.model_dump(),
            message=f"Experiment {run.experiment_id} saved",
        )
