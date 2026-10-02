"""
DataWise AI — Missing Value Intelligence & Safe KNN Imputation Engine

Evaluates:
  - Missing percentage
  - Distribution skewness & presence of extreme outliers
  - Correlation structure between features
  - Computational feasibility for KNN / IterativeImputer
  - Time-series continuity properties
Recommends optimal imputation strategy with clear, explainable justification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


class MissingValueDecision:
    def __init__(
        self,
        column: str,
        dtype: str,
        missing_count: int,
        missing_pct: float,
        recommended_strategy: str,
        alternative_strategies: List[str],
        rationale: str,
        knn_suitability: Dict[str, Any],
        requires_human_approval: bool = False,
    ) -> None:
        self.column = column
        self.dtype = dtype
        self.missing_count = missing_count
        self.missing_pct = missing_pct
        self.recommended_strategy = recommended_strategy
        self.alternative_strategies = alternative_strategies
        self.rationale = rationale
        self.knn_suitability = knn_suitability
        self.requires_human_approval = requires_human_approval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "column": self.column,
            "dtype": self.dtype,
            "missing_count": self.missing_count,
            "missing_pct": self.missing_pct,
            "recommended_strategy": self.recommended_strategy,
            "alternative_strategies": self.alternative_strategies,
            "rationale": self.rationale,
            "knn_suitability": self.knn_suitability,
            "requires_human_approval": self.requires_human_approval,
        }


class MissingValueDecisionEngine:
    """
    Intelligent engine evaluating statistical traits to assign justifiable imputation tactics.
    """

    def __init__(self, df: pd.DataFrame, is_time_series: bool = False) -> None:
        self.df = df
        self.total_rows = len(df)
        self.is_time_series = is_time_series
        self.num_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
        ]

    def evaluate_missingness(self) -> Dict[str, Any]:
        decisions: List[Dict[str, Any]] = []
        total_missing_cells = int(self.df.isna().sum().sum())
        total_cells = self.df.size
        overall_missing_pct = round((total_missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

        for col in self.df.columns:
            s = self.df[col]
            missing_count = int(s.isna().sum())
            if missing_count == 0:
                continue

            missing_pct = round((missing_count / self.total_rows * 100), 2)
            dtype_str = str(s.dtype)
            is_num = col in self.num_cols

            decision = self._decide_strategy_for_column(col, s, is_num, missing_count, missing_pct, dtype_str)
            decisions.append(decision.to_dict())

        return {
            "total_missing_cells": total_missing_cells,
            "overall_missing_pct": overall_missing_pct,
            "columns_with_missing": len(decisions),
            "decisions": decisions,
        }

    def _decide_strategy_for_column(
        self,
        col: str,
        series: pd.Series,
        is_num: bool,
        missing_count: int,
        missing_pct: float,
        dtype_str: str,
    ) -> MissingValueDecision:
        # Case 1: Critical Missingness (> 60%) -> Recommend Column Drop with Human Approval
        if missing_pct >= 60.0:
            return MissingValueDecision(
                column=col,
                dtype=dtype_str,
                missing_count=missing_count,
                missing_pct=missing_pct,
                recommended_strategy="drop_column",
                alternative_strategies=["impute_with_missing_indicator", "constant_indicator"],
                rationale=(
                    f"Column '{col}' has {missing_pct}% missing values. Imputing over 60% of entries "
                    f"introduces substantial synthetic variance and can mislead ML estimators. "
                    f"Dropping the column is recommended, but requires human confirmation."
                ),
                knn_suitability={"suitable": False, "reason": "Missingness exceeds 60% threshold for stable neighbor estimation."},
                requires_human_approval=True,
            )

        # Case 2: Time Series Specific Imputation
        if self.is_time_series:
            return MissingValueDecision(
                column=col,
                dtype=dtype_str,
                missing_count=missing_count,
                missing_pct=missing_pct,
                recommended_strategy="interpolation",
                alternative_strategies=["forward_fill", "backward_fill", "median"],
                rationale=(
                    f"In temporal datasets, linear interpolation or forward-fill preserves chronological sequence "
                    f"without leaking future time-step information."
                ),
                knn_suitability={"suitable": False, "reason": "Time-series autocorrelation makes local interpolation preferred."},
                requires_human_approval=False,
            )

        # Case 3: Categorical / Discrete Features
        if not is_num:
            if missing_pct < 5.0:
                return MissingValueDecision(
                    column=col,
                    dtype=dtype_str,
                    missing_count=missing_count,
                    missing_pct=missing_pct,
                    recommended_strategy="most_frequent",
                    alternative_strategies=["constant_unknown"],
                    rationale=(
                        f"Low missingness ({missing_pct}%) in categorical '{col}'. Mode imputation (most frequent category) "
                        f"minimizes distortion to frequency dynamics."
                    ),
                    knn_suitability={"suitable": False, "reason": "Categorical feature; standard distance metrics not directly applicable."},
                    requires_human_approval=False,
                )
            else:
                return MissingValueDecision(
                    column=col,
                    dtype=dtype_str,
                    missing_count=missing_count,
                    missing_pct=missing_pct,
                    recommended_strategy="constant_unknown",
                    alternative_strategies=["most_frequent"],
                    rationale=(
                        f"Moderate/high categorical missingness ({missing_pct}% in '{col}'). Imputing a dedicated 'Unknown' category "
                        f"allows tree models to learn whether absence of data holds informative signal."
                    ),
                    knn_suitability={"suitable": False, "reason": "Categorical feature."},
                    requires_human_approval=False,
                )

        # Case 4: Numerical Features (Evaluate Skewness & KNN Feasibility)
        clean_s = series.dropna()
        skewness = float(clean_s.skew()) if len(clean_s) > 3 else 0.0
        knn_info = self._assess_knn_suitability(col, missing_pct)

        # If heavily skewed (> 1.0 or < -1.0) -> Median is mathematically superior to Mean
        if abs(skewness) > 1.0:
            recommended = "median"
            alts = ["knn", "mean"] if knn_info["suitable"] else ["mean", "iterative"]
            rationale = (
                f"Feature '{col}' is skewed (skewness = {round(skewness, 2)}). The arithmetic mean would be pulled by the tail; "
                f"median imputation represents the central 50th percentile without distortion from extreme observations."
            )
        else:
            # Symmetric / normal distribution
            recommended = "mean"
            alts = ["median", "knn"] if knn_info["suitable"] else ["median", "iterative"]
            rationale = (
                f"Feature '{col}' exhibits near-symmetric distribution (skewness = {round(skewness, 2)}). "
                f"Mean imputation preserves the expected value and population variance minimally."
            )

        # If KNN is exceptionally well-suited (moderate size, high correlation), present it in rationale
        if knn_info["suitable"] and missing_pct > 3.0:
            rationale += f" Note: KNNImputer is also viable ({knn_info['reason']})."

        return MissingValueDecision(
            column=col,
            dtype=dtype_str,
            missing_count=missing_count,
            missing_pct=missing_pct,
            recommended_strategy=recommended,
            alternative_strategies=alts,
            rationale=rationale,
            knn_suitability=knn_info,
            requires_human_approval=False,
        )

    def _assess_knn_suitability(self, target_col: str, missing_pct: float) -> Dict[str, Any]:
        """
        Calculates whether KNN imputation is computationally safe and statistically sound.
        Avoids KNN if dataset is too large (> 10,000 rows) or correlations are negligible.
        """
        # 1. Dataset size check
        if self.total_rows > 10000:
            return {
                "suitable": False,
                "reason": f"Dataset size ({self.total_rows:,} rows) exceeds 10,000 threshold. KNN pairwise distance calculation is O(N²) and computationally prohibitive.",
            }

        # 2. Number of numerical features
        num_candidates = [c for c in self.num_cols if c != target_col]
        if len(num_candidates) < 3:
            return {
                "suitable": False,
                "reason": f"Only {len(num_candidates)} other numerical features available. KNN requires at least 3 dimensions for reliable nearest-neighbor distance estimation.",
            }

        # 3. Missingness check
        if missing_pct > 25.0:
            return {
                "suitable": False,
                "reason": f"Missingness ({missing_pct}%) is too high for KNN. Nearest neighbor distance metrics degrade when features contain frequent co-occurring missingness.",
            }

        # 4. Correlation check with other numerical features
        try:
            corr_s = self.df[self.num_cols].corr()[target_col].abs().drop(target_col, errors="ignore")
            max_corr = float(corr_s.max()) if len(corr_s) > 0 else 0.0
            if max_corr < 0.25:
                return {
                    "suitable": False,
                    "reason": f"Maximum correlation with other numerical features is low (r = {round(max_corr, 2)}). KNN offers little advantage over median when features are orthogonal.",
                }
            return {
                "suitable": True,
                "reason": f"Dataset size is manageable ({self.total_rows:,} rows) and feature shows strong correlation with peers (max r = {round(max_corr, 2)}).",
            }
        except Exception:
            return {"suitable": True, "reason": "Sufficient numerical dimensions and manageable dataset size."}
