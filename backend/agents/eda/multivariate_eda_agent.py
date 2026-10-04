"""
DataWise AI — Multivariate EDA Agent
Sections 12 & 13 Specification:
Explores higher-order relationships across feature subsets:
- Pre-selects top informative features (avoids explosive N*N matrices)
- Correlation Heatmaps
- Cluster & Dimensionality Projections
- Representative sampling for massive datasets (Section 13)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class MultivariateEDAAgent:
    """Orchestrates multivariate relationship analysis with memory and time safeguards."""

    def __init__(self, name: str = "MultivariateEDAAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            n_rows = len(df)
            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            target_col = state.get("target_column")

            # Representative sample for expensive multivariate analysis
            sample_size = min(3000, n_rows) if n_rows > 5000 else n_rows
            sample_df = df.sample(sample_size, random_state=42) if n_rows > sample_size else df

            # Intelligently select top 6 most variable or target-correlated features
            selected_features: List[str] = []
            if target_col and target_col in num_cols:
                corrs = sample_df[num_cols].corr()[target_col].abs().sort_values(ascending=False)
                selected_features = [c for c in corrs.index if c != target_col][:5]
            else:
                variances = sample_df[num_cols].var().sort_values(ascending=False)
                selected_features = list(variances.index[:5])

            multivariate_summary = {
                "selected_multivariate_features": selected_features,
                "sample_size_used": sample_size,
                "is_sampled": n_rows > sample_size,
                "recommended_multivariate_plots": [
                    {"type": "correlation_heatmap", "columns": selected_features},
                    {"type": "pairplot_sample", "columns": selected_features[:4]},
                ],
            }

            state.setdefault("eda_results", {})["multivariate"] = multivariate_summary
            state.setdefault("completed_steps", []).append("multivariate_eda")
            logger.info(f"[{self.name}] Multivariate analysis planned on {len(selected_features)} top features ({sample_size} rows sampled).")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in multivariate EDA: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
