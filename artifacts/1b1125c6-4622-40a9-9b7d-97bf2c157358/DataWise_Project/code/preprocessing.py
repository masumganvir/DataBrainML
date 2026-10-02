"""
DataWise AI — Preprocessing Pipeline Definition
"""

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

NUMERICAL_FEATURES = []
CATEGORICAL_FEATURES = []


def create_preprocessor() -> ColumnTransformer:
    """Builds leak-free ColumnTransformer for numerical and categorical features."""
    transformers = []
    if NUMERICAL_FEATURES:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("num", num_pipe, NUMERICAL_FEATURES))

    if CATEGORICAL_FEATURES:
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("cat", cat_pipe, CATEGORICAL_FEATURES))

    return ColumnTransformer(transformers=transformers, remainder="drop")