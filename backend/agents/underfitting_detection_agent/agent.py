"""
DataWise AI — Underfitting Detection Agent (Section 27)
Detects high bias, poor training & validation performance, underpowered models,
and generates structured remediation recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.underfitting_detection_agent.schemas import UnderfittingReport


class UnderfittingDetectionAgent(BaseAgent):
    """Underfitting Detection & Bias Diagnostic Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Underfitting Detection Agent")

    def diagnose(
        self,
        train_score: float,
        val_score: float,
        model_name: str = "CandidateModel",
        metric_name: str = "accuracy",
        benchmark_threshold: float = 0.65,
    ) -> UnderfittingReport:
        """Deterministically evaluates training and validation scores for high bias."""
        gap = round(abs(train_score - val_score), 4)
        is_underfit = train_score < benchmark_threshold and val_score < benchmark_threshold

        root_causes: List[str] = []
        actions: List[str] = []

        if is_underfit:
            if train_score < 0.50:
                severity = "severe"
                evidence = (
                    f"Model '{model_name}' exhibits severe high bias: training {metric_name} ({train_score:.3f}) "
                    f"and validation {metric_name} ({val_score:.3f}) are both substantially below acceptable benchmark ({benchmark_threshold:.3f})."
                )
            else:
                severity = "moderate"
                evidence = (
                    f"Model '{model_name}' exhibits moderate underfitting: training {metric_name} ({train_score:.3f}) "
                    f"and validation {metric_name} ({val_score:.3f}) fail to reach target benchmark ({benchmark_threshold:.3f})."
                )

            root_causes.extend([
                "Model capacity is insufficient for the underlying data complexity.",
                "Feature set lacks sufficient predictive signal or informative interactions.",
                "Regularization parameter (e.g. L1/L2 penalty, max_depth) may be excessively restrictive.",
            ])
            actions.extend([
                "Switch to higher-capacity non-linear model families (e.g. Gradient Boosting, Random Forest).",
                "Engineer non-linear features, interaction terms, or polynomial transformations.",
                "Relax regularization hyperparameters (e.g. reduce C, increase max_depth, reduce min_samples_split).",
            ])
        else:
            severity = "none"
            evidence = f"Model '{model_name}' demonstrates satisfactory fit: train {train_score:.3f}, val {val_score:.3f}."

        return UnderfittingReport(
            is_underfitting=is_underfit,
            train_score=train_score,
            val_score=val_score,
            score_gap=gap,
            severity=severity,
            evidence=evidence,
            root_causes=root_causes,
            recommended_actions=actions,
            model_name=model_name,
        )

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        train_score = float(params.get("train_score", 0.75))
        val_score = float(params.get("val_score", 0.72))
        model_name = params.get("model_name", "PrimaryModel")
        metric_name = params.get("metric_name", "score")

        report = self.diagnose(
            train_score=train_score,
            val_score=val_score,
            model_name=model_name,
            metric_name=metric_name,
        )

        status = "warning" if report.is_underfitting else "success"
        summary = (
            f"Underfitting detected for {model_name} (Severity: {report.severity})"
            if report.is_underfitting
            else f"No underfitting detected for {model_name}."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status=status,
            data={"underfitting_report": report.model_dump()},
            summary=summary,
            warnings=[report.evidence] if report.is_underfitting else [],
        )
