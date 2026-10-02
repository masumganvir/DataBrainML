"""
DataWise AI — Preprocessing: Categorical Encoding Builder
"""

from typing import Any, Dict, List, Optional
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder


def create_categorical_encoder(
    method: str = "onehot",
    handle_unknown: str = "ignore",
    max_categories: Optional[int] = 30,
) -> Any:
    """Instantiates a leak-safe scikit-learn encoder."""
    m = method.lower()
    if m in ("onehot", "one_hot", "ohe"):
        return OneHotEncoder(
            handle_unknown=handle_unknown,
            sparse_output=False,
            max_categories=max_categories,
        )
    elif m in ("ordinal", "label"):
        return OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
    elif m in ("target", "target_encoder"):
        try:
            from sklearn.preprocessing import TargetEncoder
            return TargetEncoder(smooth="auto", cv=5)
        except Exception:
            return OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
