"""
DataWise AI — Overfitting & Underfitting Detection Agent
Compares training, cross-validation, and holdout test scores to diagnose
high variance (overfitting) or high bias (underfitting). Recommends actionable remedies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class OverfittingDetectionAgent(BaseAgent):
    """Overfitting, Underfitting, and Bias-Variance Diagnostic Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Overfitting Detection Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        train_score = float(params.get("train_score", 0.90))
        cv_score = float(params.get("cv_score", 0.82))
        test_score = float(params.get("test_score", 0.81))

        gap = round(train_score - test_score, 4)
        remedies: List[str] = []
        diagnosis: Literal["OPTIMAL", "SLIGHT_OVERFITTING", "SEVERE_OVERFITTING", "UNDERFITTING"] = "OPTIMAL"

        # Underfitting check: both train and test scores poor
        if train_score < 0.65 and test_score < 0.65:
            diagnosis = "UNDERFITTING"
            remedies = [
                "Increase model capacity (e.g. increase tree depth, add estimators)",
                "Engineer richer non-linear interaction features",
                "Decrease regularization strength (e.g. lower alpha / L2 penalty)",
                "Try gradient boosted trees instead of simple linear models",
            ]
            summary = f"Underfitting detected (High Bias): Training score ({train_score:.3f}) and Test score ({test_score:.3f}) are both low."
        elif gap > 0.15:
            diagnosis = "SEVERE_OVERFITTING"
            remedies = [
                "Increase regularization (L1/L2 penalty, lower max_depth)",
                "Apply feature selection to prune uninformative noise features",
                "Increase cross-validation folds and check for data leakage",
                "Add dropout or limit maximum tree leaf nodes",
            ]
            summary = f"Severe Overfitting detected (High Variance): Training score ({train_score:.3f}) outpaces Test score ({test_score:.3f}) by {gap:.1%} gap."
        elif gap > 0.05:
            diagnosis = "SLIGHT_OVERFITTING"
            remedies = [
                "Mild regularization recommended (e.g. min_samples_split=5)",
                "Early stopping during boosting rounds",
            ]
            summary = f"Mild Overfitting observed: Generalization gap is {gap:.1%}. Model acceptable for deployment with slight tuning."
        else:
            diagnosis = "OPTIMAL"
            remedies = ["Model is well-calibrated; no structural bias or variance intervention required."]
            summary = f"Generalization balance is Optimal: Train ({train_score:.3f}) and Test ({test_score:.3f}) gap is within healthy bounds ({gap:.1%})."

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="warning" if "SEVERE" in diagnosis else "success",
            data={
                "diagnosis": diagnosis,
                "train_score": train_score,
                "test_score": test_score,
                "generalization_gap": gap,
                "recommended_remedies": remedies,
            },
            summary=summary,
        )
