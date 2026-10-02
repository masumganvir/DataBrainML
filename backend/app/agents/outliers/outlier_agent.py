"""
DataWise AI — Outlier Agent
Specialized agent for anomaly detection and outlier impact analysis.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.outliers import OutlierAnalyzer, analyze_dataset_outliers


class OutlierAgent(BaseAgent):
    """Detects univariate and multivariate anomalies using IQR, Z-Score, and Isolation Forest."""

    def __init__(self) -> None:
        super().__init__(
            name="OutlierAgent",
            role="Anomaly Detection & Outlier Specialist",
            description="Identifies extreme values, assesses outlier severity, and recommends clipping, winsorizing, or robust scaling.",
            system_prompt=(
                "You are an expert in anomaly detection and outlier treatment. "
                "Explain the statistical impact of outliers on linear models vs tree-based models. "
                "Recommend appropriate treatment strategies: clipping (IQR bounds), RobustScaler, "
                "log transformations, or isolation forest filtering."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Running outlier analysis for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        try:
            target_col = state.get("target_column")
            domain = state.get("dataset_domain")
            objective = state.get("prediction_objective")

            result = analyze_dataset_outliers(
                df=df,
                target_col=target_col,
                domain=domain,
                objective=objective,
            )
            return {
                **state,
                "outlier_report": result.get("iqr_reports", []),
                "outlier_decisions": result.get("outlier_decisions", []),
                "current_stage": "DISTRIBUTIONS",
                "completed_stages": [*state.get("completed_stages", []), "OUTLIERS"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Outlier analysis failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "OUTLIERS", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        decisions = state.get("outlier_decisions", [])
        if decisions:
            lines = [
                f"- {d['column']}: {d.get('outlier_count', 0)} ({d.get('outlier_pct', 0)}%) -> "
                f"Action: {d.get('recommended_action')} ({d.get('classified_as')}). Rationale: {d.get('rationale')}"
                for d in decisions
            ]
            return "Context-Aware Outlier Decisions:\n" + "\n".join(lines)

        reports = state.get("outlier_report", [])
        outlier_lines = [
            f"- {r['column']}: {r.get('outlier_count', 0)} outliers ({r.get('outlier_pct', 0)}%) [{r.get('severity', 'mild')}]"
            for r in reports if r.get("outlier_count", 0) > 0
        ]
        return "Outliers detected:\n" + ("\n".join(outlier_lines) if outlier_lines else "No severe outliers detected.")
