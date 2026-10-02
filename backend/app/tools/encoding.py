"""
DataWise AI — Categorical Encoding Recommendation & Transformation Tool

Analyzes cardinality, ordering, and category distributions to recommend optimal encoding:
  - Binary (2 unique values) -> Binary/Ordinal mapping
  - Low cardinality (<= 10 categories) -> OneHotEncoder (handle_unknown='ignore')
  - High cardinality (> 10 categories) -> FrequencyEncoder, TargetEncoder, or TopKOneHot
  - High cardinality ID / hash (near unique) -> Flag as drop or entity embedding
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

import pandas as pd


class EncodingRecommender:
    """Recommends and configures categorical encoding strategies."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.cat_cols = [
            str(c) for c in df.columns
            if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]) or str(df[c].dtype) == "category")
        ]

    def recommend_for_column(self, col: str) -> Dict[str, Any]:
        """Evaluates a single column and determines the best encoding."""
        s = self.df[col].dropna()
        n_rows = len(self.df)
        n_unique = int(s.nunique())
        unique_ratio = round(n_unique / n_rows, 4) if n_rows > 0 else 0.0

        top_categories = list(s.value_counts().head(10).index.astype(str))

        # 1. Binary column
        if n_unique == 2:
            return {
                "column": col,
                "strategy": "binary_mapping",
                "encoder_class": "OrdinalEncoder",
                "cardinality": 2,
                "parameters": {"handle_unknown": "use_encoded_value", "unknown_value": -1},
                "top_categories": top_categories,
                "rationale": f"Column '{col}' has exactly 2 unique values. Binary/Ordinal mapping creates a single compact numeric column without expanding dimensionality.",
            }

        # 2. Extreme / Identifier cardinality (>80% unique or > 100 in small data)
        if unique_ratio > 0.8 and n_rows >= 50:
            return {
                "column": col,
                "strategy": "drop_or_id",
                "encoder_class": "None",
                "cardinality": n_unique,
                "parameters": {},
                "top_categories": top_categories,
                "rationale": f"Column '{col}' has extremely high cardinality ({n_unique} unique values in {n_rows} rows). Likely an identifier or noisy feature. Dropping or feature hashing recommended.",
            }

        # 3. Low to Moderate Cardinality (3 to 10 unique)
        if n_unique <= 10:
            return {
                "column": col,
                "strategy": "one_hot",
                "encoder_class": "OneHotEncoder",
                "cardinality": n_unique,
                "parameters": {"handle_unknown": "ignore", "sparse_output": False},
                "top_categories": top_categories,
                "rationale": f"Column '{col}' has low cardinality ({n_unique} unique categories). OneHotEncoder with handle_unknown='ignore' creates interpretable orthogonal dummy features safely.",
            }

        # 4. Moderate-to-High Cardinality (11 to 50 unique)
        if n_unique <= 50:
            return {
                "column": col,
                "strategy": "target_or_frequency",
                "encoder_class": "TargetEncoder",
                "cardinality": n_unique,
                "parameters": {"smooth": "auto", "cv": 5},
                "top_categories": top_categories,
                "rationale": f"Column '{col}' has moderate cardinality ({n_unique} unique categories). TargetEncoder or frequency encoding avoids exploding dimensionality while retaining category signals.",
            }

        # 5. Very High Cardinality (> 50 unique)
        return {
            "column": col,
            "strategy": "frequency_or_top_k",
            "encoder_class": "OneHotEncoder",
            "cardinality": n_unique,
            "parameters": {"max_categories": 15, "handle_unknown": "infrequent_if_exist"},
            "top_categories": top_categories,
            "rationale": f"Column '{col}' has high cardinality ({n_unique} categories). Recommending Top-15 OneHotEncoder with an 'infrequent' category bin to prevent memory blowup.",
        }

    def recommend_all(self) -> List[Dict[str, Any]]:
        """Generates encoding recommendations for all categorical columns."""
        return [self.recommend_for_column(col) for col in self.cat_cols]


def recommend_categorical_encoding(
    df: pd.DataFrame, target_column: Optional[str] = None, **kwargs: Any
) -> List[Dict[str, Any]]:
    """Helper entry point for categorical encoding recommendations."""
    recommender = EncodingRecommender(df)
    return recommender.recommend_all()

