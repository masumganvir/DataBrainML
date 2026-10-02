"""
Agentic AutoML Intelligence Platform — Retraining Decision Engine
Evaluates telemetry, drift indicators, and ground truth to govern model updates safely.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RetrainingAction(str, Enum):
    CONTINUE = "CONTINUE"                         # Model remains stable, no action required
    ONLINE_UPDATE = "ONLINE_UPDATE"               # Incremental update via partial_fit
    RETRAIN = "RETRAIN"                           # Full automated retraining pipeline
    WAIT_FOR_MORE_DATA = "WAIT_FOR_MORE_DATA"     # Drift detected but insufficient labeled data
    ASK_USER = "ASK_USER"                         # High ambiguity or high-cost impact; requires human-in-the-loop
    ROLLBACK = "ROLLBACK"                         # Severe degradation; revert to previous version immediately


class RetrainingDecision(BaseModel):
    action: RetrainingAction
    severity: str                                 # low | medium | high | critical
    justification: str
    drift_score: float = 0.0
    performance_degradation: float = 0.0
    new_data_count: int = 0
    requires_human_approval: bool = False
    suggested_retraining_strategy: Optional[str] = None


class RetrainingDecisionEngine:
    """Intelligently arbitrates continuous model maintenance and retraining decisions."""

    @classmethod
    def evaluate(
        cls,
        drift_report: Dict[str, Any],
        concept_drift_report: Optional[Dict[str, Any]] = None,
        new_samples_count: int = 0,
        model_supports_online: bool = False,
        min_retrain_samples: int = 1000,
        min_incremental_samples: int = 50,
        human_approval_required: bool = False,
    ) -> RetrainingDecision:
        drift_severity = drift_report.get("overall_severity", "none")
        drift_detected = drift_report.get("drift_detected", False)
        drift_ratio = drift_report.get("drift_ratio", 0.0)

        perf_degradation = 0.0
        concept_severity = "none"
        if concept_drift_report:
            perf_degradation = concept_drift_report.get("performance_degradation", 0.0)
            concept_severity = concept_drift_report.get("severity", "none")

        # 1. Critical Performance Drop -> Check Rollback or Human Alert
        if perf_degradation > 0.25:
            return RetrainingDecision(
                action=RetrainingAction.ROLLBACK,
                severity="critical",
                justification=f"Severe production performance drop ({perf_degradation:.1%}). Immediate rollback to previous stable checkpoint recommended.",
                drift_score=drift_ratio,
                performance_degradation=perf_degradation,
                new_data_count=new_samples_count,
                requires_human_approval=True,
            )

        # 2. Concept or Feature Drift Detected
        if concept_severity in ("high", "medium") or drift_severity == "high":
            if new_samples_count >= min_retrain_samples:
                action = RetrainingAction.ASK_USER if human_approval_required else RetrainingAction.RETRAIN
                return RetrainingDecision(
                    action=action,
                    severity="high",
                    justification=f"High drift detected (severity: {drift_severity}, degraded: {perf_degradation:.1%}) with {new_samples_count} accumulated samples. Full retraining recommended.",
                    drift_score=drift_ratio,
                    performance_degradation=perf_degradation,
                    new_data_count=new_samples_count,
                    requires_human_approval=human_approval_required,
                    suggested_retraining_strategy="full_retraining_with_hyperparameter_optimization",
                )
            elif model_supports_online and new_samples_count >= min_incremental_samples:
                return RetrainingDecision(
                    action=RetrainingAction.ONLINE_UPDATE,
                    severity="medium",
                    justification=f"Moderate drift with incremental algorithm support. Triggering safe shadow-validated partial_fit.",
                    drift_score=drift_ratio,
                    performance_degradation=perf_degradation,
                    new_data_count=new_samples_count,
                    requires_human_approval=False,
                    suggested_retraining_strategy="incremental_partial_fit",
                )
            else:
                return RetrainingDecision(
                    action=RetrainingAction.WAIT_FOR_MORE_DATA,
                    severity="medium",
                    justification=f"Drift detected but insufficient sample volume ({new_samples_count}/{min_retrain_samples}). Continuing monitoring buffer.",
                    drift_score=drift_ratio,
                    performance_degradation=perf_degradation,
                    new_data_count=new_samples_count,
                    requires_human_approval=False,
                )

        # 3. Minor Drift with Incremental Support
        if drift_severity == "medium" and model_supports_online and new_samples_count >= min_incremental_samples:
            return RetrainingDecision(
                action=RetrainingAction.ONLINE_UPDATE,
                severity="low",
                justification=f"Minor drift detected. Applying incremental online update.",
                drift_score=drift_ratio,
                performance_degradation=perf_degradation,
                new_data_count=new_samples_count,
                requires_human_approval=False,
            )

        # 4. Normal Stable Operation
        return RetrainingDecision(
            action=RetrainingAction.CONTINUE,
            severity="low",
            justification="Model distributions and performance metrics are stable within tolerance thresholds.",
            drift_score=drift_ratio,
            performance_degradation=perf_degradation,
            new_data_count=new_samples_count,
            requires_human_approval=False,
        )


retraining_decision_engine = RetrainingDecisionEngine()
