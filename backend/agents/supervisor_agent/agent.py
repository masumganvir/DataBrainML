"""
DataWise AI — Supervisor Agent
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.supervisor_agent.schemas import WorkflowPlan


class SupervisorAgent(BaseAgent):
    """Supervisor Agent: Dynamically routes the end-to-end data science lifecycle."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Supervisor Agent")

    def determine_workflow(
        self,
        problem_type: str = "classification",
        user_objective: Optional[str] = None,
        has_outliers: bool = True,
        needs_retraining: bool = False,
    ) -> WorkflowPlan:
        """Dynamically builds the execution sequence based on problem type and dataset characteristics."""
        if needs_retraining:
            order = ["monitoring", "retraining", "model_comparison", "deployment"]
        elif problem_type == "clustering":
            order = [
                "intake", "profiling", "data_quality", "missing_values", "outlier",
                "encoding", "scaling", "transformation", "feature_engineering",
                "feature_selection", "problem_type", "model_selection", "training",
                "evaluation", "explainability", "visualization", "artifact_generation",
            ]
        elif problem_type == "anomaly_detection":
            order = [
                "intake", "profiling", "data_quality", "missing_values", "outlier",
                "encoding", "scaling", "feature_selection", "problem_type",
                "model_selection", "training", "evaluation", "visualization",
            ]
        else:
            # Standard supervised classification or regression pipeline
            order = [
                "intake", "profiling", "data_quality", "outlier", "missing_values",
                "encoding", "scaling", "transformation", "feature_engineering",
                "feature_selection", "leakage_detection", "problem_type",
                "model_selection", "training", "hyperparameter_tuning",
                "evaluation", "overfitting_detection", "explainability",
                "robustness", "model_comparison", "visualization",
                "artifact_generation", "deployment", "monitoring",
            ]

        return WorkflowPlan(
            objective=user_objective or f"End-to-End AutoML for {problem_type}",
            problem_type=problem_type,
            selected_agents=order,
            execution_order=order,
        )

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        problem_type = params.get("problem_type", "classification")
        objective = params.get("objective")
        has_outliers = params.get("has_outliers", True)
        needs_retraining = params.get("needs_retraining", False)

        plan = self.determine_workflow(
            problem_type=problem_type,
            user_objective=objective,
            has_outliers=has_outliers,
            needs_retraining=needs_retraining,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"workflow_plan": plan.model_dump()},
            summary=f"Planned workflow for {problem_type} consisting of {len(plan.execution_order)} stages.",
        )
