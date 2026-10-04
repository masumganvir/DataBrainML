"""
DataWise AI — Feature Relationship Agent
Computes feature-to-target dependency metrics (Mutual Information & ANOVA/Correlation).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

from backend.agents.eda.eda_state import EDAState


class FeatureRelationshipAgent:
    """Ranks feature-to-target associations with mutual information and correlation."""

    def __init__(self, name: str = "FeatureRelationshipAgent"):
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
                return state

            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            features = [c for c in num_cols if c != target_col]
            if not features:
                return state

            sample_size = min(3000, len(df))
            sample_df = df[features + [target_col]].dropna()
            if len(sample_df) > sample_size:
                sample_df = sample_df.sample(sample_size, random_state=42)

            X = sample_df[features]
            y = sample_df[target_col]
            task_type = state.get("task_type", "Classification")

            # Mutual Information
            relationships: List[Dict[str, Any]] = []
            try:
                if "Regression" in task_type:
                    mi_scores = mutual_info_regression(X, y, random_state=42)
                else:
                    mi_scores = mutual_info_classif(X, y, random_state=42)

                corrs = X.corrwith(y) if pd.api.types.is_numeric_dtype(y) else pd.Series(0.0, index=features)

                for idx, col in enumerate(features):
                    relationships.append({
                        "feature": col,
                        "mutual_information": round(float(mi_scores[idx]), 4),
                        "linear_correlation": round(float(corrs.get(col, 0.0)), 4),
                    })

                relationships.sort(key=lambda x: x["mutual_information"], reverse=True)
            except Exception as mi_err:
                logger.debug(f"Mutual info pass note: {mi_err}")

            state["feature_relationships"] = {
                "ranked_relationships": relationships[:15],
                "top_features": [r["feature"] for r in relationships[:5]],
            }
            state.setdefault("completed_steps", []).append("feature_relationships")
            logger.info(f"[{self.name}] Ranked {len(relationships)} feature associations to target '{target_col}'.")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in feature relationships: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
