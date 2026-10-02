"""
DataWise AI — Distribution Transformation Tool

Recommends non-linear variance-stabilizing and normalizing transformations:
  - PowerTransformer (Yeo-Johnson & Box-Cox)
  - FunctionTransformer (log1p / log)
  - QuantileTransformer (uniform / normal)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class TransformationRecommender:
    """Recommends non-linear transformations for skewed continuous features."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.num_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
            and df[c].dropna().nunique() > 5
        ]

    def recommend_for_column(self, col: str) -> Dict[str, Any]:
        """Recommends transformation for a single column."""
        s = self.df[col].dropna()
        if len(s) < 10:
            return {"column": col, "transformation": "none", "transformer_class": "None", "parameters": {}}

        skew_val = float(s.skew())
        min_val = float(s.min())

        # Low skewness: no transformation needed
        if abs(skew_val) <= 0.75:
            return {
                "column": col,
                "transformation": "none",
                "transformer_class": "None",
                "skewness": round(skew_val, 3),
                "parameters": {},
                "rationale": f"Feature '{col}' has low skewness ({skew_val:.2f}). No transformation necessary.",
            }

        # High positive skew with zeros
        if skew_val > 0.75:
            if min_val == 0.0:
                return {
                    "column": col,
                    "transformation": "log1p",
                    "transformer_class": "FunctionTransformer",
                    "skewness": round(skew_val, 3),
                    "parameters": {"func": "np.log1p", "inverse_func": "np.expm1"},
                    "rationale": f"Feature '{col}' is heavily right-skewed ({skew_val:.2f}) and includes zeros. log1p transformation compresses large values safely.",
                }
            elif min_val > 0.0:
                return {
                    "column": col,
                    "transformation": "box-cox_or_yeo-johnson",
                    "transformer_class": "PowerTransformer",
                    "skewness": round(skew_val, 3),
                    "parameters": {"method": "yeo-johnson", "standardize": False},
                    "rationale": f"Feature '{col}' is right-skewed ({skew_val:.2f}) and strictly positive. PowerTransformer optimizes lambda to maximize normality.",
                }
            else:
                return {
                    "column": col,
                    "transformation": "yeo-johnson",
                    "transformer_class": "PowerTransformer",
                    "skewness": round(skew_val, 3),
                    "parameters": {"method": "yeo-johnson", "standardize": False},
                    "rationale": f"Feature '{col}' is skewed ({skew_val:.2f}) with negative numbers. Yeo-Johnson transformation supports negative domains.",
                }
        else:
            # Negative (left) skew
            return {
                "column": col,
                "transformation": "yeo-johnson",
                "transformer_class": "PowerTransformer",
                "skewness": round(skew_val, 3),
                "parameters": {"method": "yeo-johnson", "standardize": False},
                "rationale": f"Feature '{col}' is left-skewed ({skew_val:.2f}). Yeo-Johnson normalizes negative skewness.",
            }

    def recommend_all(self) -> List[Dict[str, Any]]:
        """Recommends transformations for all numerical features."""
        return [self.recommend_for_column(col) for col in self.num_cols]


def recommend_transformations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Helper entry point for transformation recommendations."""
    recommender = TransformationRecommender(df)
    return recommender.recommend_all()
