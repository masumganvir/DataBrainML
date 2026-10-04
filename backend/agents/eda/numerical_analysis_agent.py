"""
DataWise AI — Numerical Analysis Agent
Audits statistical properties of continuous features: magnitude, variance, and scale recommendations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class NumericalAnalysisAgent:
    """Evaluates numeric feature scales, dispersions, and optimal normalization strategies."""

    def __init__(self, name: str = "NumericalAnalysisAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            target_col = state.get("target_column")
            features = [c for c in num_cols if c != target_col]

            num_summary: Dict[str, Any] = {}
            for col in features:
                series = df[col].dropna()
                if series.empty:
                    continue

                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                std = float(series.std()) if len(series) > 1 else 0.0

                # Check if RobustScaler is best (presence of outliers or high IQR variance)
                outlier_flags = ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum()
                if outlier_flags > 0.01 * len(series):
                    rec_scaler = "RobustScaler (Resistant to extreme observations)"
                elif float(series.min()) >= 0 and float(series.max()) <= 1.0:
                    rec_scaler = "PassThrough (Already bounded [0, 1])"
                else:
                    rec_scaler = "StandardScaler (Zero mean, unit variance)"

                num_summary[col] = {
                    "mean": round(float(series.mean()), 3),
                    "std": round(std, 3),
                    "min": round(float(series.min()), 3),
                    "max": round(float(series.max()), 3),
                    "iqr": round(float(iqr), 3),
                    "recommended_scaler": rec_scaler,
                }

            state["numerical_summary"] = num_summary
            state.setdefault("completed_steps", []).append("numerical_analysis")
            logger.info(f"[{self.name}] Analyzed {len(num_summary)} continuous numeric features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Numerical analysis error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
