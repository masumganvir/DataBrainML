"""
DataWise AI — Preprocessing: Feature Scaling Builder
"""

from typing import Any
from sklearn.preprocessing import (
    MaxAbsScaler,
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
)


def create_feature_scaler(method: str = "standard") -> Any:
    """Instantiates a scikit-learn numerical feature scaler."""
    m = method.lower()
    if m in ("standard", "zscore", "standardscaler"):
        return StandardScaler()
    elif m in ("minmax", "min_max", "minmaxscaler"):
        return MinMaxScaler()
    elif m in ("robust", "robustscaler"):
        return RobustScaler()
    elif m in ("maxabs", "maxabsscaler"):
        return MaxAbsScaler()
    elif m in ("none", "passthrough"):
        return "passthrough"
    return StandardScaler()
