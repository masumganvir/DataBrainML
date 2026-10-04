"""
DataWise AI — Categorical Analysis Agent
Audits categorical distributions, cardinality, rare category risks, and recommends optimal encodings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class CategoricalAnalysisAgent:
    """Analyzes discrete and categorical features to guide encoding and grouping."""

    def __init__(self, name: str = "CategoricalAnalysisAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            cat_cols = state.get("categorical_columns") or list(df.select_dtypes(exclude=[np.number]).columns)
            target_col = state.get("target_column")
            features = [c for c in cat_cols if c != target_col]

            cat_summary: Dict[str, Any] = {}
            for col in features:
                series = df[col].dropna()
                if series.empty:
                    continue

                val_counts = series.value_counts(normalize=True)
                n_unique = int(series.nunique())

                # Check rare classes (< 2% frequency)
                rare_classes = val_counts[val_counts < 0.02].index.tolist()

                # Recommend encoding
                if n_unique == 2:
                    recommended_encoding = "BinaryEncoder (0/1 map)"
                elif n_unique <= 7:
                    recommended_encoding = "OneHotEncoder(drop='first', sparse_output=False)"
                elif n_unique <= 20:
                    recommended_encoding = "OneHotEncoder with Rare Category Grouping"
                else:
                    recommended_encoding = "TargetEncoder / FrequencyEncoder (High Cardinality)"

                cat_summary[col] = {
                    "cardinality": n_unique,
                    "top_categories": {str(k): round(float(v) * 100, 1) for k, v in val_counts.head(5).items()},
                    "rare_categories_count": len(rare_classes),
                    "imbalance_ratio": round(float(val_counts.iloc[0] / max(0.001, val_counts.iloc[-1])), 2) if len(val_counts) > 1 else 1.0,
                    "recommended_encoding": recommended_encoding,
                }

            state["categorical_summary"] = cat_summary
            state.setdefault("completed_steps", []).append("categorical_analysis")
            logger.info(f"[{self.name}] Audited {len(cat_summary)} categorical features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Categorical analysis error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
