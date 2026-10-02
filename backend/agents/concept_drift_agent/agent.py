"""
Agentic AutoML Intelligence Platform — Concept Drift Agent
Analyzes production metrics as true ground truth labels arrive.
"""

from __future__ import annotations

import numpy as np
from agents.base import BaseAgent, AgentInput, AgentOutput
from monitoring.drift_engine import drift_engine


class ConceptDriftAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ConceptDriftAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        predictions = input_data.parameters.get("predictions", [])
        ground_truth = input_data.parameters.get("ground_truth", [])
        baseline_metric = input_data.parameters.get("baseline_metric", 0.85)
        metric_name = input_data.parameters.get("metric_name", "f1")
        problem_type = input_data.parameters.get("problem_type", "classification")

        if not predictions or not ground_truth:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"concept_drift_detected": False, "reason": "No ground truth available yet."},
                summary="Awaiting ground truth labels for concept drift analysis.",
            )

        res = drift_engine.compute_concept_drift(
            predictions=np.array(predictions),
            ground_truth=np.array(ground_truth),
            baseline_metric_value=float(baseline_metric),
            metric_name=metric_name,
            problem_type=problem_type,
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="warning" if res.get("concept_drift_detected") else "success",
            data=res,
            summary=f"Concept drift: {res.get('severity', 'none').upper()}. Current metric: {res.get('current_production_metric')} vs baseline {res.get('baseline_metric')}.",
        )
