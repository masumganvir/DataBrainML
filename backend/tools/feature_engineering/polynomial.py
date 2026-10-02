"""
DataWise AI — Feature Engineering: Polynomial Expansions
"""

from typing import Any, Dict, List, Tuple
import pandas as pd


def generate_polynomial_features(
    df: pd.DataFrame,
    columns: List[str],
    degree: int = 2,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Generates squared powers for justified non-linear continuous columns."""
    engineered = pd.DataFrame(index=df.index)
    meta: List[Dict[str, Any]] = []

    for col in columns:
        if col in df.columns:
            feat_name = f"{col}_pow_{degree}"
            engineered[feat_name] = df[col] ** degree
            meta.append({
                "name": feat_name,
                "formula": f"{col} ** {degree}",
                "reason": f"Models non-linear quadratic acceleration / diminishing returns in {col}.",
                "expected_benefit": "Improves linear model fit for parabolic curves.",
            })

    return engineered, meta
