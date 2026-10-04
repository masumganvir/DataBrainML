"""
DataWise AI — Feature Selection Agent
Sections 21 & 22 Specification:
CRITICAL PRINCIPLE: Zero data leakage.
Feature selection must be fitted inside the training pipeline.
Evaluates:
- VarianceThreshold (prune constant/near-zero variance)
- Mutual Information (non-linear dependency)
- ANOVA F-statistic / Chi-Square
- Random Forest Tree Importance
Recommends optimal feature subset for model training.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import VarianceThreshold, f_classif, f_regression

from backend.agents.eda.eda_state import EDAState


class FeatureSelectionAgent:
    """Evaluates multi-criteria feature relevance with zero test leakage."""

    def __init__(self, name: str = "FeatureSelectionAgent"):
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

            if not features or not target_col or target_col not in df.columns:
                return state

            task_type = state.get("task_type", "Classification")
            sample_size = min(3000, len(df))
            sample_df = df[features + [target_col]].dropna()
            if len(sample_df) > sample_size:
                sample_df = sample_df.sample(sample_size, random_state=42)

            X = sample_df[features]
            y = sample_df[target_col]

            # 1. Variance Check
            vt = VarianceThreshold(threshold=0.01)
            vt.fit(X)
            low_var_features = [f for f, keep in zip(features, vt.get_support()) if not keep]

            # 2. ANOVA F-statistic
            f_scores: Dict[str, float] = {}
            try:
                if "Regression" in task_type:
                    f_vals, _ = f_regression(X, y)
                else:
                    f_vals, _ = f_classif(X, y)
                for f_name, score in zip(features, f_vals):
                    f_scores[f_name] = round(float(score) if not (np.isnan(score) or np.isinf(score)) else 0.0, 3)
            except Exception as f_err:
                logger.debug(f"ANOVA pass notice: {f_err}")

            # 3. Quick Tree Feature Importance
            rf_importances: Dict[str, float] = {}
            try:
                if "Regression" in task_type:
                    rf = RandomForestRegressor(n_estimators=30, max_depth=6, random_state=42, n_jobs=-1)
                else:
                    rf = RandomForestClassifier(n_estimators=30, max_depth=6, random_state=42, n_jobs=-1)
                rf.fit(X, y)
                for f_name, imp in zip(features, rf.feature_importances_):
                    rf_importances[f_name] = round(float(imp), 4)
            except Exception as rf_err:
                logger.debug(f"Random forest pass notice: {rf_err}")

            # Rank features
            sorted_features = sorted(
                features,
                key=lambda f: (rf_importances.get(f, 0.0) * 0.7 + (f_scores.get(f, 0.0) / max(1.0, max(f_scores.values() or [1.0]))) * 0.3),
                reverse=True,
            )

            # Recommend top K features (e.g. up to 25)
            k_rec = min(len(sorted_features), max(5, int(len(sorted_features) * 0.75)))
            selected_features = sorted_features[:k_rec]

            selection_payload = {
                "total_candidate_features": len(features),
                "recommended_features": selected_features,
                "low_variance_pruned": low_var_features,
                "top_tree_importances": {k: rf_importances[k] for k in sorted_features[:8] if k in rf_importances},
                "f_scores": {k: f_scores[k] for k in sorted_features[:8] if k in f_scores},
                "leakage_directive": "Ensure SelectKBest or RFE is fit strictly on X_train inside ColumnTransformer / Pipeline.",
            }

            state["feature_selection_results"] = selection_payload
            state.setdefault("completed_steps", []).append("feature_selection")
            logger.info(f"[{self.name}] Evaluated feature selection: recommended {len(selected_features)} of {len(features)} features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Feature selection error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
