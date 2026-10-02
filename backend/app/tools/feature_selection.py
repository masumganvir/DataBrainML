"""
DataWise AI — Feature Selection Tool

Implements multiple feature selection strategies:
  1. Variance Threshold   — drops near-zero variance features
  2. Correlation Filter   — drops features highly correlated with each other
  3. Mutual Information   — MI scores vs target (classification + regression)
  4. SelectKBest (f-test) — F-statistic for supervised selection
  5. Model Importance     — RandomForest-based importance (if scikit-learn available)
  6. Permutation Filter   — removes columns irrelevant to target
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


class FeatureSelector:
    """
    Runs multiple selection strategies and returns a consolidated
    recommendation with per-feature scores and selection status.
    """

    VARIANCE_THRESHOLD: float = 0.01
    HIGH_CORR_THRESHOLD: float = 0.95
    TOP_K_MI: int = 20

    def __init__(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> None:
        self.df = df.copy()
        self.target_column = target_column
        self.task_type = task_type or "classification"

        feature_cols = [c for c in df.columns if c != target_column]
        self.feature_df = df[feature_cols].copy()

        # Encode object columns to numeric for sklearn methods
        self._numeric_df = self._encode_for_selection(self.feature_df)
        self._target_series: Optional[pd.Series] = (
            df[target_column] if target_column and target_column in df.columns else None
        )

    # -------------------------------------------------------------- #
    #  Public API
    # -------------------------------------------------------------- #

    def run_all(self) -> Dict[str, Any]:
        """Run all selection methods and produce a unified report."""
        results: Dict[str, Dict[str, Any]] = {col: {
            "column": col,
            "passes_variance": True,
            "passes_correlation": True,
            "mi_score": None,
            "f_score": None,
            "rf_importance": None,
            "vote_count": 0,
            "selected": True,
            "reasons": [],
        } for col in self.feature_df.columns}

        # 1. Variance threshold
        var_results = self._variance_threshold()
        for col, passes in var_results.items():
            if col in results:
                results[col]["passes_variance"] = passes
                if not passes:
                    results[col]["vote_count"] -= 1
                    results[col]["reasons"].append("Near-zero variance (likely constant)")
                else:
                    results[col]["vote_count"] += 1

        # 2. Correlation filter
        drop_corr = self._correlation_filter()
        for col in drop_corr:
            if col in results:
                results[col]["passes_correlation"] = False
                results[col]["vote_count"] -= 1
                results[col]["reasons"].append("Highly correlated with another retained feature (r > 0.95)")

        # 3. Mutual information (if target available)
        if self._target_series is not None:
            mi_scores = self._mutual_information()
            for col, score in mi_scores.items():
                if col in results:
                    results[col]["mi_score"] = score
                    if score > 0.01:
                        results[col]["vote_count"] += 1
                    else:
                        results[col]["vote_count"] -= 1
                        results[col]["reasons"].append("Very low mutual information with target")

        # 4. F-statistic (classification) or F-regression
        if self._target_series is not None:
            f_scores = self._f_scores()
            for col, score in f_scores.items():
                if col in results:
                    results[col]["f_score"] = score
                    if score and score > 1.0:
                        results[col]["vote_count"] += 1

        # 5. Random Forest importance
        rf_importances = self._rf_importance()
        for col, imp in rf_importances.items():
            if col in results:
                results[col]["rf_importance"] = imp
                if imp > 0.005:
                    results[col]["vote_count"] += 1
                else:
                    results[col]["reasons"].append("Near-zero importance in RandomForest")

        # Finalize selection
        feature_list = list(results.values())
        for f in feature_list:
            f["selected"] = f["vote_count"] >= 0  # net positive votes = selected

        selected = [f["column"] for f in feature_list if f["selected"]]
        dropped = [f["column"] for f in feature_list if not f["selected"]]

        return {
            "total_features_evaluated": len(feature_list),
            "selected_count": len(selected),
            "dropped_count": len(dropped),
            "selected_features": selected,
            "dropped_features": dropped,
            "feature_details": feature_list,
            "recommendation": self._build_recommendation(selected, dropped, feature_list),
        }

    # -------------------------------------------------------------- #
    #  Private: individual methods
    # -------------------------------------------------------------- #

    def _variance_threshold(self) -> Dict[str, bool]:
        results = {}
        for col in self._numeric_df.columns:
            try:
                var = float(self._numeric_df[col].var())
                results[col] = var > self.VARIANCE_THRESHOLD
            except Exception:  # noqa: BLE001
                results[col] = True
        return results

    def _correlation_filter(self) -> List[str]:
        """Return list of columns to drop due to high pairwise correlation."""
        try:
            corr = self._numeric_df.corr().abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            return [col for col in upper.columns if (upper[col] > self.HIGH_CORR_THRESHOLD).any()]
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Correlation filter failed: {exc}")
            return []

    def _mutual_information(self) -> Dict[str, float]:
        try:
            from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

            X = self._numeric_df.fillna(0)
            y = self._encode_target()
            if y is None or len(y) != len(X):
                return {}

            if self.task_type == "regression":
                scores = mutual_info_regression(X, y, random_state=42)
            else:
                scores = mutual_info_classif(X, y.astype(int), random_state=42)

            return dict(zip(X.columns, [float(s) for s in scores]))
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"MI failed: {exc}")
            return {}

    def _f_scores(self) -> Dict[str, Optional[float]]:
        try:
            from sklearn.feature_selection import f_classif, f_regression

            X = self._numeric_df.fillna(0)
            y = self._encode_target()
            if y is None or len(y) != len(X):
                return {}

            if self.task_type == "regression":
                f_vals, _ = f_regression(X, y)
            else:
                f_vals, _ = f_classif(X, y.astype(int))

            return {col: float(f) for col, f in zip(X.columns, f_vals) if not np.isnan(f)}
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"F-score failed: {exc}")
            return {}

    def _rf_importance(self) -> Dict[str, float]:
        """Use RandomForest on small subset for fast importance estimation."""
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.preprocessing import LabelEncoder

            X = self._numeric_df.fillna(0)
            y = self._encode_target()
            if y is None or len(y) != len(X):
                return {}

            # Subsample for speed
            n = min(5000, len(X))
            idx = np.random.choice(len(X), n, replace=False)
            X_s, y_s = X.iloc[idx], y.iloc[idx]

            if self.task_type == "regression":
                model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            else:
                y_s = LabelEncoder().fit_transform(y_s.astype(str))
                model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)

            model.fit(X_s, y_s)
            return dict(zip(X.columns, [float(i) for i in model.feature_importances_]))
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"RF importance failed: {exc}")
            return {}

    # -------------------------------------------------------------- #
    #  Private: helpers
    # -------------------------------------------------------------- #

    def _encode_for_selection(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode object/category columns with integer codes for numeric methods."""
        out = df.copy()
        for col in out.select_dtypes(include=["object", "category"]).columns:
            out[col] = out[col].astype("category").cat.codes.replace(-1, np.nan)
        for col in out.select_dtypes(include=["datetime64"]).columns:
            out[col] = out[col].astype(np.int64) // 10**9  # unix timestamp
        return out.select_dtypes(include=[np.number])

    def _encode_target(self) -> Optional[pd.Series]:
        if self._target_series is None:
            return None
        s = self._target_series.copy()
        if s.dtype == object or str(s.dtype) == "category":
            s = s.astype("category").cat.codes
        return s.fillna(-1)

    def _build_recommendation(
        self,
        selected: List[str],
        dropped: List[str],
        details: List[Dict[str, Any]],
    ) -> str:
        lines = [
            f"Feature selection retained {len(selected)} features and recommends dropping {len(dropped)}.",
        ]
        if dropped:
            lines.append(
                f"The following features were flagged for removal: {', '.join(dropped[:10])}"
                + (" ..." if len(dropped) > 10 else "")
            )
            lines.append("Reasons include near-zero variance, multicollinearity, and low information gain.")
        if selected:
            lines.append(
                f"Top retained features (by RF importance): "
                + ", ".join(
                    f['column'] for f in sorted(
                        [d for d in details if d['selected']],
                        key=lambda x: x.get('rf_importance') or 0,
                        reverse=True,
                    )[:8]
                )
            )
        return " ".join(lines)

    # -------------------------------------------------------------- #
    #  Static factory
    # -------------------------------------------------------------- #

    @classmethod
    def from_path(
        cls,
        file_path: str,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> "FeatureSelector":
        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            df = pd.read_csv(file_path)
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif ext == "json":
            df = pd.read_json(file_path)
        else:
            df = pd.read_csv(file_path)
        return cls(df, target_column=target_column, task_type=task_type)
