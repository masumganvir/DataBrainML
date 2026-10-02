"""
DataWise AI — Feature Engineering: Dimensionless Ratios
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def generate_ratio_features(
    df: pd.DataFrame,
    pairs: List[Tuple[str, str]],
    eps: float = 1e-6,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Generates zero-division safe feature ratios."""
    engineered = pd.DataFrame(index=df.index)
    meta: List[Dict[str, Any]] = []

    for num_col, denom_col in pairs:
        if num_col in df.columns and denom_col in df.columns:
            feat_name = f"{num_col}_per_{denom_col}"
            engineered[feat_name] = df[num_col] / (df[denom_col].abs() + eps)
            meta.append({
                "name": feat_name,
                "formula": f"{num_col} / ({denom_col} + {eps})",
                "reason": f"Normalizes {num_col} by {denom_col} to capture intensity / density.",
                "expected_benefit": "Removes scale effects and highlights per-unit efficiency.",
            })

    return engineered, meta
