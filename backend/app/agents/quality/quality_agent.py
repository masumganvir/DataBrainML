"""
DataWise AI — Quality Agent
Specialized agent for data hygiene, missing value audits, and duplicate detection.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.quality import QualityAnalyzer, analyze_data_quality


class QualityAgent(BaseAgent):
    """Analyzes missing values, detects duplicate records, and grades dataset hygiene."""

    def __init__(self) -> None:
        super().__init__(
            name="QualityAgent",
            role="Data Hygiene & Quality Assurance Specialist",
            description="Detects missing data patterns, MCAR/MAR/MNAR risks, duplicate records, and recommends remediation.",
            system_prompt=(
                "You are an expert in data quality and data cleaning. "
                "Evaluate missing value ratios and duplicate rows. "
                "Warn against data leakage or high missingness (>50%) that warrants dropping columns. "
                "Always advise whether imputation (mean, median, mode, KNN, iterative) or dropping is best."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Running quality audit for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        try:
            result = analyze_data_quality(df)
            return {
                **state,
                "missing_value_report": result.get("missing_reports", []),
                "duplicate_report": result.get("duplicates", {}),
                "current_stage": "HUMAN_APPROVAL",
                "completed_stages": [*state.get("completed_stages", []), "QUALITY"],
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Quality audit failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "QUALITY", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        missing = state.get("missing_value_report", [])
        dup = state.get("duplicate_report", {})
        missing_summary = [
            f"- {m['column']}: {m['missing_pct']}% missing ({m['missing_count']} rows) -> Recommended: {m.get('recommended_strategy')}"
            for m in missing if m.get("missing_pct", 0) > 0
        ]
        return (
            f"Duplicate Rows: {dup.get('duplicate_count', 0)} ({dup.get('duplicate_pct', 0.0)}%)\n"
            f"Columns with Missing Values:\n" + ("\n".join(missing_summary) if missing_summary else "No missing values found.")
        )
