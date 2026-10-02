"""
DataWise AI — Feature Engineering: Multiplicative Interactions
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def generate_interaction_features(
    df: pd.DataFrame,
    pairs: List[Tuple[str, str]],
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Generates pairwise multiplication interactions."""
    engineered = pd.DataFrame(index=df.index)
    meta: List[Dict[str, Any]] = []

    for col_a, col_b in pairs:
        if col_a in df.columns and col_b in df.columns:
            feat_name = f"{col_a}_x_{col_b}"
            engineered[feat_name] = df[col_a] * df[col_b]
            meta.append({
                "name": feat_name,
                "formula": f"{col_a} * {col_b}",
                "reason": f"Captures synergistic joint effect between {col_a} and {col_b}.",
                "expected_benefit": "Enables linear and tree models to capture non-additive joint variation.",
            })

    return engineered, meta
