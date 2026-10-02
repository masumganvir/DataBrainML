"""
DataWise AI — sklearn Pipeline Builder

Constructs a complete sklearn ColumnTransformer + Pipeline definition based on
approved preprocessing decisions. Also generates ready-to-run Python code.
"""

from __future__ import annotations

import textwrap
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger


class PipelineBuilder:
    """
    Translates approved preprocessing decisions into a structured pipeline
    definition and generates executable Python code.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
        encoding_plan: Optional[List[Dict[str, Any]]] = None,
        scaling_plan: Optional[List[Dict[str, Any]]] = None,
        transformation_plan: Optional[List[Dict[str, Any]]] = None,
        imputation_decisions: Optional[Dict[str, str]] = None,
        selected_features: Optional[List[str]] = None,
    ) -> None:
        self.df = df
        self.target_column = target_column
        self.task_type = task_type or "classification"

        feature_cols = [c for c in df.columns if c != target_column]
        self.encoding_plan = encoding_plan or []
        self.scaling_plan = scaling_plan or []
        self.transformation_plan = transformation_plan or []
        self.imputation_decisions = imputation_decisions or {}
        self.selected_features = selected_features or feature_cols

        # Column categorisation
        self.numerical_cols = [
            c for c in self.selected_features
            if pd.api.types.is_numeric_dtype(df[c])
        ]
        self.categorical_cols = [
            c for c in self.selected_features
            if not pd.api.types.is_numeric_dtype(df[c])
        ]

    # -------------------------------------------------------------- #
    #  Public API
    # -------------------------------------------------------------- #

    def build(self) -> Dict[str, Any]:
        """Return the pipeline definition dict and generated Python code."""
        num_imputer = self._resolve_numerical_imputer()
        cat_imputer = self._resolve_categorical_imputer()
        scaler = self._resolve_scaler()
        encoder = self._resolve_encoder()
        transformer = self._resolve_transformer()

        definition: Dict[str, Any] = {
            "target_column": self.target_column,
            "task_type": self.task_type,
            "numerical_columns": self.numerical_cols,
            "categorical_columns": self.categorical_cols,
            "numerical_imputer": num_imputer,
            "numerical_scaler": scaler,
            "numerical_transformer": transformer,
            "categorical_imputer": cat_imputer,
            "categorical_encoder": encoder,
            "selected_features": self.selected_features,
        }

        code = self._generate_pipeline_code(definition)
        definition["generated_code"] = code

        return definition

    # -------------------------------------------------------------- #
    #  Private: resolve strategies
    # -------------------------------------------------------------- #

    def _resolve_numerical_imputer(self) -> str:
        # Use the most common imputation strategy from imputation_decisions
        strategies = [v for v in self.imputation_decisions.values() if v in ("median", "mean", "zero")]
        if not strategies:
            return "median"
        return max(set(strategies), key=strategies.count)

    def _resolve_categorical_imputer(self) -> str:
        strategies = [v for v in self.imputation_decisions.values() if v in ("mode", "constant", "most_frequent")]
        if not strategies:
            return "most_frequent"
        return max(set(strategies), key=strategies.count)

    def _resolve_scaler(self) -> Optional[str]:
        if not self.scaling_plan:
            return "StandardScaler"
        # Use most commonly recommended scaler
        names = [p.get("recommended_scaler", "StandardScaler") for p in self.scaling_plan]
        return max(set(names), key=names.count) if names else "StandardScaler"

    def _resolve_encoder(self) -> str:
        if not self.encoding_plan:
            return "OneHotEncoder"
        names = [p.get("recommended_encoder", "OneHotEncoder") for p in self.encoding_plan]
        return max(set(names), key=names.count) if names else "OneHotEncoder"

    def _resolve_transformer(self) -> Optional[str]:
        if not self.transformation_plan:
            return None
        # If any column needs power transform, use it
        for plan in self.transformation_plan:
            if plan.get("recommended_transform") in ("PowerTransformer", "QuantileTransformer"):
                return plan["recommended_transform"]
        return None

    # -------------------------------------------------------------- #
    #  Private: code generation
    # -------------------------------------------------------------- #

    def _generate_pipeline_code(self, definition: Dict[str, Any]) -> str:  # noqa: C901
        target = definition["target_column"]
        task = definition["task_type"]
        num_cols = definition["numerical_columns"]
        cat_cols = definition["categorical_columns"]
        num_imputer = definition["numerical_imputer"]
        cat_imputer = definition["categorical_imputer"]
        scaler = definition["numerical_scaler"]
        encoder = definition["categorical_encoder"]
        transformer = definition.get("numerical_transformer")

        # Determine default model
        model_map = {
            "classification": "RandomForestClassifier(n_estimators=100, random_state=42)",
            "regression": "RandomForestRegressor(n_estimators=100, random_state=42)",
            "clustering": "KMeans(n_clusters=3, random_state=42)",
            "time_series": "RandomForestRegressor(n_estimators=100, random_state=42)",
        }
        model_str = model_map.get(task, "RandomForestClassifier()")

        # Numerical pipeline steps
        num_steps: List[str] = [f"('imputer', SimpleImputer(strategy='{num_imputer}'))"]
        if transformer:
            num_steps.append(f"('transformer', {transformer}())")
        if scaler:
            num_steps.append(f"('scaler', {scaler}())")

        # Categorical pipeline steps
        ohe_kwargs = "handle_unknown='ignore'" if encoder == "OneHotEncoder" else ""
        cat_steps: List[str] = [
            f"('imputer', SimpleImputer(strategy='{cat_imputer}'))",
            f"('encoder', {encoder}({ohe_kwargs}))",
        ]

        num_steps_str = ",\n            ".join(num_steps)
        cat_steps_str = ",\n            ".join(cat_steps)

        imports = textwrap.dedent(f"""\
            # ═══════════════════════════════════════════════════════════════════
            #  DataWise AI — Auto-Generated sklearn Pipeline
            #  Task: {task}  |  Target: {target}
            # ═══════════════════════════════════════════════════════════════════

            import pandas as pd
            import numpy as np
            from sklearn.pipeline import Pipeline
            from sklearn.compose import ColumnTransformer
            from sklearn.impute import SimpleImputer
            from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
            from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
            from sklearn.preprocessing import PowerTransformer, QuantileTransformer
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.metrics import classification_report, mean_squared_error
        """)

        if task == "classification":
            imports += "from sklearn.ensemble import RandomForestClassifier\n"
        elif task == "regression":
            imports += "from sklearn.ensemble import RandomForestRegressor\n"
        elif task == "clustering":
            imports += "from sklearn.cluster import KMeans\n"

        body = textwrap.dedent(f"""

            # ── Load Dataset ─────────────────────────────────────────────────
            df = pd.read_csv("your_dataset.csv")  # Replace with actual path

            # ── Define Features and Target ───────────────────────────────────
            NUMERICAL_COLS   = {num_cols!r}
            CATEGORICAL_COLS = {cat_cols!r}
            TARGET           = {target!r}

            X = df[NUMERICAL_COLS + CATEGORICAL_COLS]
            y = df[TARGET]

            # ── Train/Test Split ─────────────────────────────────────────────
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # ── Numerical Preprocessing Pipeline ─────────────────────────────
            numerical_pipeline = Pipeline(steps=[
                {num_steps_str}
            ])

            # ── Categorical Preprocessing Pipeline ───────────────────────────
            categorical_pipeline = Pipeline(steps=[
                {cat_steps_str}
            ])

            # ── ColumnTransformer ────────────────────────────────────────────
            preprocessor = ColumnTransformer(
                transformers=[
                    ("num", numerical_pipeline, NUMERICAL_COLS),
                    ("cat", categorical_pipeline, CATEGORICAL_COLS),
                ],
                remainder="drop",
            )

            # ── Full Model Pipeline ──────────────────────────────────────────
            full_pipeline = Pipeline(steps=[
                ("preprocessor", preprocessor),
                ("model", {model_str}),
            ])

            # ── Train ────────────────────────────────────────────────────────
            full_pipeline.fit(X_train, y_train)

            # ── Evaluate ─────────────────────────────────────────────────────
        """)

        if task == "classification":
            body += textwrap.dedent("""\
                y_pred = full_pipeline.predict(X_test)
                print(classification_report(y_test, y_pred))

                cv_scores = cross_val_score(full_pipeline, X, y, cv=5, scoring='f1_weighted')
                print(f"CV F1-Weighted: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
            """)
        elif task == "regression":
            body += textwrap.dedent("""\
                y_pred = full_pipeline.predict(X_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                print(f"Test RMSE: {rmse:.4f}")

                cv_scores = cross_val_score(full_pipeline, X, y, cv=5, scoring='r2')
                print(f"CV R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
            """)
        else:
            body += "print('Model fitted. Inspect full_pipeline for predictions.')\n"

        return imports + body

    # -------------------------------------------------------------- #
    #  Static factory
    # -------------------------------------------------------------- #

    @classmethod
    def from_path(
        cls,
        file_path: str,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
        **kwargs: Any,
    ) -> "PipelineBuilder":
        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            df = pd.read_csv(file_path)
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif ext == "json":
            df = pd.read_json(file_path)
        return cls(df, target_column=target_column, task_type=task_type, **kwargs)


def build_column_transformer(
    numerical_cols: Optional[List[str]] = None,
    categorical_cols: Optional[List[str]] = None,
    scaler: str = "StandardScaler",
    encoder: str = "OneHotEncoder",
) -> Any:
    """Builds a scikit-learn ColumnTransformer for numerical and categorical features."""
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, OneHotEncoder, OrdinalEncoder

    scaler_map = {
        "StandardScaler": StandardScaler(),
        "MinMaxScaler": MinMaxScaler(),
        "RobustScaler": RobustScaler(),
    }
    encoder_map = {
        "OneHotEncoder": OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        "OrdinalEncoder": OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
    }

    transformers = []
    if numerical_cols:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", scaler_map.get(scaler, StandardScaler())),
        ])
        transformers.append(("num", num_pipe, numerical_cols))

    if categorical_cols:
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", encoder_map.get(encoder, OneHotEncoder(handle_unknown="ignore", sparse_output=False))),
        ])
        transformers.append(("cat", cat_pipe, categorical_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def build_pipeline(preprocessor: Any, estimator: Any) -> Any:
    """Constructs a scikit-learn Pipeline linking preprocessor and estimator."""
    from sklearn.pipeline import Pipeline
    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

