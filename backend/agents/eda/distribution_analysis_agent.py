"""
DataWise AI — Distribution Analysis Agent
Analyzes empirical feature distributions, skewness, kurtosis, and suggests appropriate transformations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from scipy import stats

from backend.agents.eda.eda_state import EDAState


class DistributionAnalysisAgent:
    """Classifies feature distributions and suggests variance-stabilizing transformations."""

    def __init__(self, name: str = "DistributionAnalysisAgent"):
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

            dist_summary: Dict[str, Any] = {}
            for col in features:
                series = df[col].dropna()
                if len(series) < 10 or series.nunique() <= 2:
                    continue

                skew = float(series.skew())
                kurt = float(series.kurtosis())
                min_val = float(series.min())

                # Recommend transformation
                if abs(skew) > 1.5:
                    if min_val > 0:
                        rec_transform = "Log1p or Box-Cox (severe positive skew)"
                    else:
                        rec_transform = "Yeo-Johnson (supports zero/negative values)"
                elif abs(skew) > 0.75:
                    rec_transform = "RobustScaler or PowerTransform"
                else:
                    rec_transform = "StandardScaler (approximately symmetric)"

                dist_summary[col] = {
                    "skewness": round(skew, 3),
                    "kurtosis": round(kurt, 3),
                    "symmetry": "Highly Skewed" if abs(skew) > 1.0 else ("Moderately Skewed" if abs(skew) > 0.5 else "Symmetric"),
                    "recommended_transformation": rec_transform,
                }

            state["distribution_summary"] = dist_summary
            state.setdefault("completed_steps", []).append("distribution_analysis")
            logger.info(f"[{self.name}] Analyzed distributions for {len(dist_summary)} numeric features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Distribution analysis error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
