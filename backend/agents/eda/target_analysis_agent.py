"""
DataWise AI — Target Analysis Agent
Sections 13 & 26 Specification:
Audits target variable dynamics:
- Classification: Class distributions, minority representation, imbalance ratio, class weights needed.
- Regression: Continuous distribution, skewness, zero-inflation, target transformation requirement.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class TargetAnalysisAgent:
    """Specialized analyzer for objective variable distribution and learning challenges."""

    def __init__(self, name: str = "TargetAnalysisAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            target_col = state.get("target_column")
            if not target_col or target_col not in df.columns:
                logger.warning(f"[{self.name}] No valid target column found in state/dataset.")
                return state

            series = df[target_col].dropna()
            n_unique = int(series.nunique())
            is_numeric = bool(pd.api.types.is_numeric_dtype(series))

            # Determine task type
            if is_numeric and n_unique > 20:
                task_type = "Regression"
            elif n_unique == 2:
                task_type = "Binary Classification"
            else:
                task_type = "Multiclass Classification"

            state["task_type"] = task_type

            if "Classification" in task_type:
                counts = series.value_counts()
                pcts = series.value_counts(normalize=True).round(4)
                majority_cnt = int(counts.iloc[0])
                minority_cnt = int(counts.iloc[-1])
                imbalance_ratio = round(majority_cnt / max(1, minority_cnt), 2)

                is_imbalanced = imbalance_ratio > 3.0
                target_payload = {
                    "task_type": task_type,
                    "target_column": target_col,
                    "classes": [str(c) for c in counts.index.tolist()],
                    "class_counts": {str(k): int(v) for k, v in counts.items()},
                    "class_percentages": {str(k): float(v) for k, v in pcts.items()},
                    "imbalance_ratio": imbalance_ratio,
                    "is_imbalanced": is_imbalanced,
                    "recommended_metric": "PR-AUC / Weighted F1" if is_imbalanced else "ROC-AUC / Accuracy",
                    "sampling_recommendation": "SMOTE / Class Weight Balancing" if is_imbalanced else "Standard StratifiedKFold",
                }
            else:
                # Regression target
                skew = float(series.skew()) if len(series) > 2 else 0.0
                zero_count = int((series == 0).sum())
                zero_pct = round((zero_count / max(1, len(series))) * 100, 2)

                target_payload = {
                    "task_type": task_type,
                    "target_column": target_col,
                    "mean": round(float(series.mean()), 3),
                    "std": round(float(series.std()), 3) if len(series) > 1 else 0.0,
                    "median": round(float(series.median()), 3),
                    "min": round(float(series.min()), 3),
                    "max": round(float(series.max()), 3),
                    "skewness": round(skew, 3),
                    "zero_count": zero_count,
                    "zero_percentage": zero_pct,
                    "recommended_metric": "R2 / RMSE",
                    "target_transformation": "Log1p Transform" if skew > 1.5 and float(series.min()) >= 0 else "None",
                }

            state["target_summary"] = target_payload
            state.setdefault("completed_steps", []).append("target_analysis")
            logger.info(f"[{self.name}] Target '{target_col}' analyzed: {task_type}.")
        except Exception as exc:
            logger.error(f"[{self.name}] Target analysis error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
