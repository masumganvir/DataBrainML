"""
DataWise AI — Numerical Feature Scaling Tool

Analyzes feature distributions, outlier presence, and bounds to recommend the optimal scaler:
  - RobustScaler: Preferred when moderate or severe outliers are present (scales by median & IQR)
  - StandardScaler: Preferred for approximately Gaussian distributions without extreme outliers
  - MinMaxScaler: Preferred for bounded values (e.g. ratios, percentages, ratings) or neural networks
  - MaxAbsScaler: Preserves zero entries in sparse or positive count data
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd


class ScalingRecommender:
    """Recommends feature scaling methods based on distributional properties and outliers."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.num_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
            and df[c].dropna().nunique() > 2
        ]

    def recommend_for_column(self, col: str) -> Dict[str, Any]:
        """Analyzes a numerical column to select the most appropriate scaler."""
        s = self.df[col].dropna()
        if len(s) < 4:
            return {
                "column": col,
                "scaler_class": "StandardScaler",
                "parameters": {},
                "has_outliers": False,
                "rationale": "Default standard scaling for small sample.",
            }

        q1 = float(np.percentile(s, 25))
        q3 = float(np.percentile(s, 75))
        iqr = q3 - q1
        outliers_iqr = int(((s < (q1 - 1.5 * iqr)) | (s > (q3 + 1.5 * iqr))).sum())
        outlier_pct = round(outliers_iqr / len(s) * 100, 2)

        min_val = float(s.min())
        max_val = float(s.max())
        skew_val = float(s.skew()) if len(s) > 2 else 0.0

        # Case 1: Outlier-heavy feature (>= 2% outliers or extreme values)
        if outlier_pct >= 2.0 or abs(skew_val) > 2.0:
            return {
                "column": col,
                "scaler_class": "RobustScaler",
                "parameters": {"with_centering": True, "with_scaling": True, "quantile_range": (25.0, 75.0)},
                "has_outliers": True,
                "outlier_percentage": outlier_pct,
                "rationale": f"Feature '{col}' contains {outlier_pct}% outliers. RobustScaler centers with the median and scales by IQR, preventing extreme values from biasing gradients.",
            }

        # Case 2: Bounded scale (e.g. 0 to 1 proportion, probability, or score)
        if 0.0 <= min_val and max_val <= 1.0 and (max_val - min_val) > 0:
            return {
                "column": col,
                "scaler_class": "MinMaxScaler",
                "parameters": {"feature_range": (0, 1)},
                "has_outliers": False,
                "outlier_percentage": outlier_pct,
                "rationale": f"Feature '{col}' lies within [0, 1]. MinMaxScaler bounds features cleanly into [0, 1] preserving proportional ratios.",
            }

        # Case 3: Standard normal / approximately symmetric
        return {
            "column": col,
            "scaler_class": "StandardScaler",
            "parameters": {"with_mean": True, "with_std": True},
            "has_outliers": False,
            "outlier_percentage": outlier_pct,
            "rationale": f"Feature '{col}' has low outlier presence ({outlier_pct}%) and symmetric structure. StandardScaler standardizes to zero mean and unit variance.",
        }

    def recommend_all(self) -> List[Dict[str, Any]]:
        """Recommends scaling for all numerical columns."""
        return [self.recommend_for_column(col) for col in self.num_cols]


def recommend_numerical_scaling(
    df: pd.DataFrame, target_column: Optional[str] = None, **kwargs: Any
) -> List[Dict[str, Any]]:
    """Helper entry point for scaling recommendations."""
    recommender = ScalingRecommender(df)
    return recommender.recommend_all()

