"""
DataWise AI — Preprocessing: Distribution Transformations
"""

from typing import Any
from sklearn.preprocessing import (
    FunctionTransformer,
    PowerTransformer,
    QuantileTransformer,
)
import numpy as np


def create_distribution_transformer(method: str = "yeo-johnson") -> Any:
    """Instantiates non-linear transformation for skewed distributions."""
    m = method.lower()
    if m in ("yeo-johnson", "yeojohnson", "power"):
        return PowerTransformer(method="yeo-johnson")
    elif m in ("log1p", "log"):
        return FunctionTransformer(np.log1p, validate=True)
    elif m in ("quantile", "quantile_normal"):
        return QuantileTransformer(output_distribution="normal", random_state=42)
    elif m in ("none", "passthrough"):
        return "passthrough"
    return "passthrough"
