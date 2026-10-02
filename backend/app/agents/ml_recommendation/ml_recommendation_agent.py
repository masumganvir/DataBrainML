"""
DataWise AI — ML Recommendation Agent
Specialized agent for algorithm selection, metric design, cross-validation schemes, and baseline modeling.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from app.agents.base.base_agent import BaseAgent
from app.state.data_science_state import DataScienceState
from app.tools.ml_recommender import MLRecommender


class MLRecommendationAgent(BaseAgent):
    """Recommends top-performing ML algorithms, evaluation metrics, and hyperparameter tuning ranges."""

    def __init__(self) -> None:
        super().__init__(
            name="MLRecommendationAgent",
            role="Machine Learning Algorithm & Strategy Consultant",
            description="Recommends optimal baseline and advanced ML models (Random Forest, XGBoost, LightGBM, Logistic/Ridge) with evaluation plans.",
            system_prompt=(
                "You are an expert ML researcher and competitive data scientist. "
                "Recommend candidate models suited to the dataset size, feature types, and task. "
                "Highlight pros and cons of linear models vs gradient boosted decision trees vs neural networks. "
                "Suggest proper cross-validation schemes (StratifiedKFold, TimeSeriesSplit, GroupKFold) "
                "and business-aligned evaluation metrics (ROC-AUC, PR-AUC, F1, RMSE, MAPE)."
            ),
        )

    def run(self, state: DataScienceState) -> DataScienceState:
        logger.info(f"[{self.name}] Generating model recommendations for session={state.get('session_id')}")

        missing_reports = state.get("missing_value_report", [])
        avg_missing = sum(r.get("missing_pct", 0) for r in missing_reports) / max(len(missing_reports), 1)
        high_sev = sum(1 for r in missing_reports if r.get("severity") in ("HIGH", "CRITICAL"))
        dup = state.get("duplicate_report", {}).get("duplicate_pct", 0.0)
        leakage_count = len(state.get("leakage_warnings", []))

        df = self._load_df(state)
        row_count = len(df) if df is not None else 0
        col_count = len(df.columns) if df is not None else 0

        try:
            recommender = MLRecommender(
                task_type=state.get("task_type") or "classification",
                row_count=row_count,
                col_count=col_count,
                missing_pct_avg=avg_missing,
                high_severity_missing=high_sev,
                duplicate_pct=float(dup),
                leakage_warnings=leakage_count,
                has_target=bool(state.get("target_column")),
            )
            result = recommender.recommend()

            return {
                **state,
                "model_recommendations": result.get("recommendations", []),
                "evaluation_plan": result.get("evaluation_plan", {}),
                "ml_readiness_score": result.get("ml_readiness", {}).get("score"),
                "ml_readiness_level": result.get("ml_readiness", {}).get("level"),
                "ml_readiness_report": result.get("ml_readiness", {}),
                "current_stage": "COMPLETE",
                "completed_stages": [*state.get("completed_stages", []), "ML_RECOMMENDATION"],
                "should_continue": False,
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] Model recommendation failed: {exc}")
            return {
                **state,
                "errors": [*state.get("errors", []), {"stage": "ML_RECOMMENDATION", "error": str(exc)}],
            }

    def _format_state_context(self, state: DataScienceState) -> str:
        recs = state.get("model_recommendations", [])
        score = state.get("ml_readiness_score")
        level = state.get("ml_readiness_level")
        models = [f"- {m.get('model_name')}: {m.get('rationale')}" for m in recs]
        return (
            f"ML Readiness: {score}/100 ({level})\n"
            f"Recommended Models:\n" + ("\n".join(models) if models else "None generated.")
        )
