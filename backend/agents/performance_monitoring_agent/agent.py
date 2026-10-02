"""
DataWise AI — PerformanceMonitoringAgent (Sections 36, 38)
Monitors real production model performance when ground truth labels arrive.
Associates ground-truth outcomes with logged inference IDs.
Computes production classification / regression metrics and detects performance degradation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    mean_absolute_error, mean_squared_error, r2_score
)
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class PerformanceReport(BaseModel):
    model_version: str
    sample_count: int
    task_type: str  # "classification" or "regression"
    metrics: Dict[str, float] = Field(default_factory=dict)
    baseline_metrics: Dict[str, float] = Field(default_factory=dict)
    degradation_detected: bool = False
    degradation_details: List[str] = Field(default_factory=list)
    action_required: str = "NONE"  # "NONE", "INVESTIGATE", "RETRAIN_RECOMMENDED"


class PerformanceMonitoringAgent(BaseAgent):
    """Computes real ground-truth performance and alerts on degradation."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="PerformanceMonitoringAgent")

    def evaluate_production_batch(
        self,
        y_true: List[Any],
        y_pred: List[Any],
        y_proba: Optional[List[float]] = None,
        task_type: str = "classification",
        baseline_metrics: Optional[Dict[str, float]] = None,
        degradation_threshold: float = 0.05,
        model_version: str = "v1.0.0",
    ) -> PerformanceReport:
        y_t = np.array(y_true)
        y_p = np.array(y_pred)
        n = len(y_t)
        base = baseline_metrics or {}
        computed: Dict[str, float] = {}
        degradations = []

        if task_type == "classification":
            acc = float(accuracy_score(y_t, y_p))
            prec = float(precision_score(y_t, y_p, average="weighted", zero_division=0))
            rec = float(recall_score(y_t, y_p, average="weighted", zero_division=0))
            f1 = float(f1_score(y_t, y_p, average="weighted", zero_division=0))

            computed["accuracy"] = round(acc, 4)
            computed["precision"] = round(prec, 4)
            computed["recall"] = round(rec, 4)
            computed["f1"] = round(f1, 4)

            if y_proba is not None and len(y_proba) == n:
                try:
                    yp = np.array(y_proba)
                    if len(np.unique(y_t)) == 2:
                        computed["roc_auc"] = round(float(roc_auc_score(y_t, yp)), 4)
                        computed["pr_auc"] = round(float(average_precision_score(y_t, yp)), 4)
                except Exception:
                    pass

            # Check degradation vs baseline
            if "f1" in base and (base["f1"] - computed["f1"]) > degradation_threshold:
                degradations.append(
                    f"F1 score dropped by {round(base['f1'] - computed['f1'], 4)} (Baseline: {base['f1']} -> Production: {computed['f1']})"
                )
            if "accuracy" in base and (base["accuracy"] - computed["accuracy"]) > degradation_threshold:
                degradations.append(
                    f"Accuracy dropped by {round(base['accuracy'] - computed['accuracy'], 4)} (Baseline: {base['accuracy']} -> Production: {computed['accuracy']})"
                )

        else:
            mae = float(mean_absolute_error(y_t, y_p))
            mse = float(mean_squared_error(y_t, y_p))
            rmse = float(np.sqrt(mse))
            r2 = float(r2_score(y_t, y_p))

            computed["mae"] = round(mae, 4)
            computed["mse"] = round(mse, 4)
            computed["rmse"] = round(rmse, 4)
            computed["r2"] = round(r2, 4)

            if "r2" in base and (base["r2"] - computed["r2"]) > degradation_threshold:
                degradations.append(
                    f"R2 dropped by {round(base['r2'] - computed['r2'], 4)} (Baseline: {base['r2']} -> Production: {computed['r2']})"
                )
            if "rmse" in base and (computed["rmse"] - base["rmse"]) > degradation_threshold:
                degradations.append(
                    f"RMSE increased by {round(computed['rmse'] - base['rmse'], 4)} (Baseline: {base['rmse']} -> Production: {computed['rmse']})"
                )

        degraded = len(degradations) > 0
        action = "RETRAIN_RECOMMENDED" if degraded else "NONE"

        return PerformanceReport(
            model_version=model_version,
            sample_count=n,
            task_type=task_type,
            metrics=computed,
            baseline_metrics=base,
            degradation_detected=degraded,
            degradation_details=degradations,
            action_required=action,
        )

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        y_true = input_data.parameters.get("y_true")
        y_pred = input_data.parameters.get("y_pred")
        y_proba = input_data.parameters.get("y_proba")
        task_type = input_data.parameters.get("task_type", "classification")
        baseline = input_data.parameters.get("baseline_metrics", {})
        version = input_data.parameters.get("model_version", "v1.0.0")

        if not y_true or not y_pred:
            return AgentOutput(
                success=False,
                errors=["y_true and y_pred are required for performance evaluation"],
            )

        try:
            report = self.evaluate_production_batch(
                y_true=y_true,
                y_pred=y_pred,
                y_proba=y_proba,
                task_type=task_type,
                baseline_metrics=baseline,
                model_version=version,
            )
            return AgentOutput(
                success=True,
                data=report.model_dump(),
                message=f"Production performance evaluated: {report.metrics}",
            )
        except Exception as e:
            logger.error(f"[PerformanceMonitoringAgent] Error: {e}")
            return AgentOutput(success=False, errors=[str(e)])
