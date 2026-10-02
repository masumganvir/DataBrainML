"""
DataWise AI — Correlation & Multicollinearity Analysis Tool

Calculates pairwise linear (Pearson) and monotonic (Spearman) relationships:
  - Detects highly correlated feature pairs (|r| > 0.85)
  - Identifies multicollinearity risks
  - Generates Variance Inflation Factor (VIF) proxies
  - Provides clear recommendations on which collinear feature to retain or drop
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


def classify_correlation_strength(abs_r: float) -> str:
    """Classifies correlation coefficient magnitude."""
    if abs_r >= 0.95:
        return "redundant_collinear"
    elif abs_r >= 0.85:
        return "very_strong"
    elif abs_r >= 0.70:
        return "strong"
    elif abs_r >= 0.40:
        return "moderate"
    else:
        return "weak"


class CorrelationAnalyzer:
    """Performs correlation scans and multicollinearity diagnosis."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Extract numerical columns with non-zero variance
        self.num_cols = [
            c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
            and df[c].dropna().nunique() > 1
        ]
        self.clean_df = df[self.num_cols].dropna() if len(self.num_cols) > 0 else pd.DataFrame()

    def calculate_matrices(self) -> Dict[str, Any]:
        """Calculates Pearson and Spearman correlation matrices."""
        if len(self.num_cols) < 2 or len(self.clean_df) < 3:
            return {"pearson": {}, "spearman": {}, "columns": []}

        pearson = self.clean_df.corr(method="pearson").round(4)
        spearman = self.clean_df.corr(method="spearman").round(4)

        return {
            "columns": self.num_cols,
            "pearson": json.loads(pearson.to_json()),
            "spearman": json.loads(spearman.to_json()),
        }

    def detect_high_correlations(self, threshold: float = 0.80) -> List[Dict[str, Any]]:
        """Finds all feature pairs with absolute correlation above threshold."""
        if len(self.num_cols) < 2 or len(self.clean_df) < 3:
            return []

        corr = self.clean_df.corr(method="pearson")
        pairs: List[Dict[str, Any]] = []

        seen_pairs = set()
        for i, col1 in enumerate(self.num_cols):
            for j, col2 in enumerate(self.num_cols):
                if i >= j:
                    continue
                pair_key = tuple(sorted([col1, col2]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                r_val = float(corr.loc[col1, col2])
                abs_r = abs(r_val)

                if abs_r >= threshold:
                    strength = classify_correlation_strength(abs_r)
                    rec = self._recommend_resolution(col1, col2, r_val)
                    pairs.append({
                        "feature_1": col1,
                        "feature_2": col2,
                        "pearson_r": round(r_val, 4),
                        "absolute_r": round(abs_r, 4),
                        "strength": strength,
                        "recommendation": rec,
                    })

        # Sort by absolute correlation descending
        pairs.sort(key=lambda x: x["absolute_r"], reverse=True)
        return pairs

    def _recommend_resolution(self, col1: str, col2: str, r_val: float) -> Dict[str, Any]:
        """Recommends which feature to keep and which to consider dropping."""
        s1 = self.df[col1]
        s2 = self.df[col2]

        miss1 = s1.isnull().sum()
        miss2 = s2.isnull().sum()

        if miss1 < miss2:
            keep = col1
            candidate_drop = col2
            reason = f"'{col1}' has fewer missing values ({miss1} vs {miss2})."
        elif miss2 < miss1:
            keep = col2
            candidate_drop = col1
            reason = f"'{col2}' has fewer missing values ({miss2} vs {miss1})."
        else:
            # Check unique values or variance
            u1 = s1.nunique()
            u2 = s2.nunique()
            if u1 >= u2:
                keep = col1
                candidate_drop = col2
                reason = f"'{col1}' has higher information granularity ({u1} vs {u2} unique values)."
            else:
                keep = col2
                candidate_drop = col1
                reason = f"'{col2}' has higher information granularity ({u2} vs {u1} unique values)."

        action = "drop_or_combine" if abs(r_val) >= 0.95 else "monitor_or_regularize"
        explanation = (
            f"Correlation r = {r_val:.2f} is exceptionally high. Keeping '{keep}' and dropping or combining '{candidate_drop}' "
            f"is recommended to prevent severe multicollinearity in linear models and neural networks. ({reason})"
            if abs(r_val) >= 0.95
            else f"Features have strong correlation (r = {r_val:.2f}). Consider tree-based models or L2 (Ridge) regularization to handle redundancy."
        )

        return {
            "action": action,
            "recommended_keep": keep,
            "candidate_drop": candidate_drop,
            "explanation": explanation,
        }


def analyze_correlations(df: pd.DataFrame, threshold: float = 0.80) -> Dict[str, Any]:
    """Helper entrypoint for running complete correlation and multicollinearity scan."""
    analyzer = CorrelationAnalyzer(df)
    matrices = analyzer.calculate_matrices()
    high_pairs = analyzer.detect_high_correlations(threshold=threshold)

    return {
        "columns_count": len(matrices["columns"]),
        "columns": matrices["columns"],
        "high_correlation_pairs": high_pairs,
        "high_correlation_count": len(high_pairs),
        "multicollinearity_risk": "HIGH" if any(p["absolute_r"] >= 0.95 for p in high_pairs) else ("MODERATE" if len(high_pairs) > 0 else "LOW"),
    }


def calculate_correlations(df: pd.DataFrame, method: str = "pearson") -> Dict[str, Any]:
    analyzer = CorrelationAnalyzer(df)
    matrices = analyzer.calculate_matrices()
    return matrices.get(method, matrices.get("pearson", {}))


def find_multicollinear_pairs(df: pd.DataFrame, threshold: float = 0.85) -> List[Dict[str, Any]]:
    analyzer = CorrelationAnalyzer(df)
    return analyzer.detect_high_correlations(threshold=threshold)

