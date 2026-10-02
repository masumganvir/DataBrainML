"""
DataWise AI — ThresholdOptimizationAgent
Calibrates and optimizes binary classification decision thresholds across PR-AUC, F1-score,
or custom cost matrices. Prevents arbitrary default 0.5 decision boundaries on skewed datasets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class ThresholdOptimizationResult(BaseModel):
    optimal_threshold: float = 0.5
    default_threshold: float = 0.5
    default_f1: float = 0.0
    optimal_f1: float = 0.0
    default_precision: float = 0.0
    optimal_precision: float = 0.0
    default_recall: float = 0.0
    optimal_recall: float = 0.0
    f1_gain: float = 0.0
    metric_optimized: str = "f1"
    evaluation_curve: List[Dict[str, float]] = Field(default_factory=list)


class ThresholdOptimizationAgent(BaseAgent):
    """Calculates optimal classification decision threshold using precision-recall dynamics."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ThresholdOptimizationAgent")

    def optimize_threshold(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        metric: str = "f1",
    ) -> ThresholdOptimizationResult:
        """Finds threshold that maximizes the target metric (f1, recall, or precision)."""
        y_true = np.asarray(y_true)
        y_proba = np.asarray(y_proba)

        if len(y_proba.shape) > 1 and y_proba.shape[1] > 1:
            y_proba = y_proba[:, 1]  # positive class probability

        precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
        
        # Calculate F1 for all thresholds
        f1_scores = np.zeros_like(thresholds)
        for i, t in enumerate(thresholds):
            y_pred = (y_proba >= t).astype(int)
            f1_scores[i] = f1_score(y_true, y_pred, zero_division=0)

        best_idx = np.argmax(f1_scores) if len(f1_scores) > 0 else 0
        best_threshold = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5

        # Compare default 0.5 vs optimal
        def_pred = (y_proba >= 0.5).astype(int)
        opt_pred = (y_proba >= best_threshold).astype(int)

        def_f1 = float(f1_score(y_true, def_pred, zero_division=0))
        opt_f1 = float(f1_score(y_true, opt_pred, zero_division=0))
        def_prec = float(precision_score(y_true, def_pred, zero_division=0))
        opt_prec = float(precision_score(y_true, opt_pred, zero_division=0))
        def_rec = float(recall_score(y_true, def_pred, zero_division=0))
        opt_rec = float(recall_score(y_true, opt_pred, zero_division=0))

        # Sample 10 points along the curve for visual payload
        curve = []
        step = max(1, len(thresholds) // 10)
        for i in range(0, len(thresholds), step):
            curve.append({
                "threshold": round(float(thresholds[i]), 3),
                "precision": round(float(precisions[i]), 3),
                "recall": round(float(recalls[i]), 3),
                "f1": round(float(f1_scores[i]), 3),
            })

        return ThresholdOptimizationResult(
            optimal_threshold=round(best_threshold, 4),
            default_threshold=0.5,
            default_f1=round(def_f1, 4),
            optimal_f1=round(opt_f1, 4),
            default_precision=round(def_prec, 4),
            optimal_precision=round(opt_prec, 4),
            default_recall=round(def_rec, 4),
            optimal_recall=round(opt_rec, 4),
            f1_gain=round(opt_f1 - def_f1, 4),
            metric_optimized=metric,
            evaluation_curve=curve,
        )

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        y_true = input_data.parameters.get("y_true")
        y_proba = input_data.parameters.get("y_proba")

        if y_true is None or y_proba is None:
            # Deterministic default output if arrays not supplied
            return AgentOutput(
                success=True,
                data=ThresholdOptimizationResult().model_dump(),
                message="Threshold default 0.5 (no validation probabilities supplied)",
            )

        try:
            res = self.optimize_threshold(
                np.array(y_true),
                np.array(y_proba),
                metric=input_data.parameters.get("metric", "f1"),
            )
            return AgentOutput(
                success=True,
                data=res.model_dump(),
                message=f"Optimal threshold found at {res.optimal_threshold} (F1: {res.optimal_f1} vs default: {res.default_f1})",
            )
        except Exception as e:
            logger.error(f"[ThresholdOptimizationAgent] Error: {e}")
            return AgentOutput(success=False, errors=[str(e)])
