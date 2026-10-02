"""
DataWise AI — ML Readiness & Target Agent
Specialized agent for target variable detection, task classification, leakage detection, and readiness auditing.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.leakage import LeakageDetector
from app.tools.target_detector import TargetDetector


class MLReadinessAgent(BaseAgent):
    """Detects target candidates, classifies ML task type, guards against data leakage, and assesses readiness."""

    def __init__(self) -> None:
        super().__init__(
            name="MLReadinessAgent",
            role="ML Readiness & Target Leakage Auditor",
            description="Identifies potential target columns, classifies supervised task types, detects target leakage, and calculates readiness scores.",
            system_prompt=(
                "You are an expert in Machine Learning readiness, problem formulation, and data leakage prevention. "
                "Detect whether the problem is binary classification, multi-class classification, or regression. "
                "Identify high-risk data leakage variables (direct target proxies, future data, ID correlations) "
                "and explain why they must be removed before training."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Assessing target and leakage for session={state.get('session_id')}")
        df = self._load_df(state)
        if df is None:
            return state

        target_candidates = state.get("target_candidates", [])
        if not state.get("target_column") and not target_candidates:
            try:
                detector = TargetDetector(df)
                result = detector.detect()
                target_candidates = [c["column"] for c in result.get("candidates", [])]
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[{self.name}] Target detection warning: {exc}")

        leakage_warnings = []
        try:
            leakage_det = LeakageDetector(
                df,
                target_column=state.get("target_column"),
                task_type=state.get("task_type"),
            )
            leakage_result = leakage_det.detect()
            leakage_warnings = leakage_result.get("warnings", [])
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{self.name}] Leakage detection warning: {exc}")

        return {
            **state,
            "target_candidates": target_candidates,
            "leakage_warnings": leakage_warnings,
            "current_stage": "PIPELINE_BUILDING",
            "completed_stages": [*state.get("completed_stages", []), "TARGET_DETECTION", "LEAKAGE_CHECK"],
        }

    def _format_state_context(self, state: DataScienceState) -> str:
        target = state.get("target_column")
        task = state.get("task_type")
        leakage = state.get("leakage_warnings", [])
        return (
            f"Target: {target or 'Auto-detecting'}\n"
            f"Task: {task or 'Undetermined'}\n"
            f"Leakage Alerts ({len(leakage)}): {[w.get('column') for w in leakage]}"
        )
