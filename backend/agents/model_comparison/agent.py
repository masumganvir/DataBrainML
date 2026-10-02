"""
DataWise AI — Model Comparison Agent
Ranks trained candidate models across multi-dimensional criteria (CV mean, variance/stability,
holdout generalization, training duration, and inference latency). Selects champion.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class ModelComparisonAgent(BaseAgent):
    """Multi-Metric Model Comparison & Champion Selection Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Model Comparison Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        trained_models: List[Dict[str, Any]] = params.get("trained_models", [])
        primary_metric = params.get("primary_metric", "cv_mean")
        max_acceptable_std = params.get("max_acceptable_cv_std", 0.08)

        if not trained_models:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                summary="Model comparison skipped: no trained model results available.",
            )

        scored_models: List[Dict[str, Any]] = []

        for m in trained_models:
            name = m.get("model_name", "Unknown")
            cv_mean = float(m.get("cv_mean", m.get("cv_score_mean", 0.0)))
            cv_std = float(m.get("cv_std", m.get("cv_score_std", 0.0)))
            test_score = float(m.get("test_score", 0.0))
            train_time = float(m.get("training_time_seconds", 0.0))

            # Composite ranking score: balances high CV performance with low variance and generalization gap
            gap = abs(float(m.get("train_score", cv_mean)) - test_score)
            stability_penalty = max(0.0, cv_std - 0.03) * 2.0
            overfit_penalty = max(0.0, gap - 0.05) * 1.5

            composite_score = round(cv_mean - stability_penalty - overfit_penalty, 4)

            scored_models.append({
                "model_name": name,
                "cv_mean": cv_mean,
                "cv_std": cv_std,
                "test_score": test_score,
                "training_time_seconds": train_time,
                "generalization_gap": round(gap, 4),
                "composite_score": composite_score,
                "is_stable": cv_std <= max_acceptable_std,
            })

        # Sort by composite score
        scored_models.sort(key=lambda x: x["composite_score"], reverse=True)
        champion = scored_models[0]

        summary = (
            f"Evaluated {len(scored_models)} models. Champion: {champion['model_name']} "
            f"(CV: {champion['cv_mean']:.4f} ± {champion['cv_std']:.4f}, Test: {champion['test_score']:.4f}, "
            f"Training: {champion['training_time_seconds']}s)."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "leaderboard": scored_models,
                "champion_model_name": champion["model_name"],
                "champion_details": champion,
            },
            summary=summary,
        )
