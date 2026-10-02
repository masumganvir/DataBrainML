"""
DataWise AI — Preprocessing Tools Package
"""

from .imputation import create_numeric_imputer, create_categorical_imputer
from .encoding import create_categorical_encoder
from .scaling import create_feature_scaler
from .transformation import create_distribution_transformer
from .splitting import split_dataset

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import Any, List


def build_column_transformer(
    numeric_features: List[str],
    categorical_features: List[str],
    impute_num_strategy: str = "median",
    impute_cat_strategy: str = "most_frequent",
    scaler_method: str = "standard",
    encoder_method: str = "onehot",
) -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer wrapping numeric and categorical sub-pipelines."""
    num_pipe = Pipeline([
        ("imputer", create_numeric_imputer(impute_num_strategy)),
        ("scaler", create_feature_scaler(scaler_method)),
    ])

    cat_pipe = Pipeline([
        ("imputer", create_categorical_imputer(impute_cat_strategy)),
        ("encoder", create_categorical_encoder(encoder_method)),
    ])

    transformers = []
    if numeric_features:
        transformers.append(("num", num_pipe, numeric_features))
    if categorical_features:
        transformers.append(("cat", cat_pipe, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


__all__ = [
    "create_numeric_imputer",
    "create_categorical_imputer",
    "create_categorical_encoder",
    "create_feature_scaler",
    "create_distribution_transformer",
    "split_dataset",
    "build_column_transformer",
]
