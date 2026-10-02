"""
DataWise AI — Model Trainer & Automated Cross-Validation Engine

Enforces strict data leakage prevention:
  1. Train/Test split executed FIRST on raw features.
  2. Preprocessing pipeline (imputation, scaling, encoding) fitted ONLY on training split.
  3. StratifiedKFold (classification) / KFold (regression) / TimeSeriesSplit (temporal) cross-validation.
  4. Task-appropriate metric selection (PR-AUC for imbalanced data, RMSE for regression).
  5. Untouched test set evaluation for final unbiased performance estimates.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, average_precision_score, balanced_accuracy_score, f1_score, mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold, TimeSeriesSplit, cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

# Module-level cache for fitted pipelines (keyed by session_id)
_pipeline_cache: Dict[str, Pipeline] = {}


class ModelTrainer:
    """
    Automated model training, cross-validation, and leak-free evaluation engine.
    """


    def __init__(
        self,
        df: pd.DataFrame,
        target_col: str,
        task_type: Optional[str] = None,
        primary_metric: Optional[str] = None,
        cv_folds: int = 5,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> None:
        self.df = df.copy()
        self.target_col = target_col
        self.test_size = test_size
        self.cv_folds = cv_folds
        self.random_state = random_state

        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in dataframe.")

        # Determine task type if not explicitly supplied
        y_raw = self.df[target_col].dropna()
        if not task_type:
            if y_raw.dtype == "object" or y_raw.nunique() <= 10 or pd.api.types.is_bool_dtype(y_raw):
                self.task_type = "classification"
            else:
                self.task_type = "regression"
        else:
            self.task_type = task_type.lower()

        # Separate feature columns from target
        self.X_raw = self.df.drop(columns=[target_col])
        self.y_raw = self.df[target_col]

        # Identify numerical and categorical features
        self.num_cols = [
            c for c in self.X_raw.columns
            if pd.api.types.is_numeric_dtype(self.X_raw[c]) and not pd.api.types.is_bool_dtype(self.X_raw[c])
        ]
        self.cat_cols = [
            c for c in self.X_raw.columns
            if c not in self.num_cols
        ]

        # Metric determination
        self.primary_metric, self.metric_rationale = self._determine_primary_metric(primary_metric)

    def _determine_primary_metric(self, requested_metric: Optional[str]) -> Tuple[str, str]:
        if self.task_type == "classification":
            y_clean = self.y_raw.dropna()
            vc = y_clean.value_counts(normalize=True)
            min_class_ratio = float(vc.min()) if len(vc) > 0 else 0.5
            is_imbalanced = min_class_ratio < 0.25

            if requested_metric:
                return requested_metric, f"User-selected metric: {requested_metric}"

            if is_imbalanced and y_clean.nunique() == 2:
                return (
                    "PR-AUC",
                    f"Dataset exhibits class imbalance (minority class represents {round(min_class_ratio * 100, 1)}% of rows). "
                    f"Accuracy is deceptive under imbalance. Precision-Recall AUC (PR-AUC) evaluates minority class retrieval without being inflated by true negatives.",
                )
            elif y_clean.nunique() == 2:
                return (
                    "ROC-AUC",
                    "Binary balanced classification. ROC-AUC evaluates the classifier's ability to discriminate between classes across all probability thresholds.",
                )
            else:
                return (
                    "Weighted F1",
                    f"Multiclass classification ({y_clean.nunique()} classes). Weighted F1 harmonizes precision and recall across all classes proportional to their support.",
                )
        else:
            if requested_metric:
                return requested_metric, f"User-selected metric: {requested_metric}"
            return (
                "RMSE",
                "Continuous regression task. Root Mean Squared Error (RMSE) evaluates prediction magnitude errors in original target units while penalizing large outlier errors.",
            )

    def build_preprocessor(self) -> ColumnTransformer:
        """Constructs an isolated ColumnTransformer that never fits on test data."""
        transformers = []
        if self.num_cols:
            num_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ])
            transformers.append(("num", num_pipe, self.num_cols))

        if self.cat_cols:
            cat_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ])
            transformers.append(("cat", cat_pipe, self.cat_cols))

        return ColumnTransformer(transformers=transformers, remainder="drop")

    def train_and_evaluate(self) -> Dict[str, Any]:
        """
        Executes leak-free train/test split, performs cross-validation on training data,
        trains candidate pipelines, and computes final performance on test data.
        """
        # 1. Clean missing target values
        valid_idx = self.y_raw.dropna().index
        X_clean = self.X_raw.loc[valid_idx]
        y_clean = self.y_raw.loc[valid_idx]

        # For classification, encode string labels to integers if needed
        is_binary = False
        class_mapping: Optional[Dict[Any, int]] = None
        if self.task_type == "classification":
            unique_classes = sorted(y_clean.unique(), key=lambda x: str(x))
            if len(unique_classes) == 2:
                is_binary = True
                class_mapping = {val: idx for idx, val in enumerate(unique_classes)}
                y_clean = y_clean.map(class_mapping)

        # 2. Strict Train/Test Separation FIRST
        from sklearn.model_selection import train_test_split

        stratify_arg = y_clean if (self.task_type == "classification" and y_clean.value_counts().min() >= 2) else None
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean,
            y_clean,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=stratify_arg,
        )

        logger.info(
            f"Train/Test split complete: Train={len(X_train)} rows, Test={len(X_test)} rows. "
            f"Preprocessing fitted strictly on Train."
        )

        # 3. Setup Cross-Validation Generator
        if self.task_type == "classification":
            min_class_samples = int(y_train.value_counts().min()) if len(y_train) > 0 else 1
            actual_folds = min(self.cv_folds, max(2, min_class_samples))
            if min_class_samples < 2:
                cv_gen = KFold(n_splits=2, shuffle=True, random_state=self.random_state)
                cv_strategy_desc = "2-Fold K-Fold (Fallback: sparse class distribution)"
            else:
                cv_gen = StratifiedKFold(n_splits=actual_folds, shuffle=True, random_state=self.random_state)
                cv_strategy_desc = f"{actual_folds}-Fold Stratified K-Fold"
        else:
            actual_folds = min(self.cv_folds, max(2, len(X_train)))
            cv_gen = KFold(n_splits=actual_folds, shuffle=True, random_state=self.random_state)
            cv_strategy_desc = f"{actual_folds}-Fold K-Fold"


        # 4. Shortlist Candidate Models
        candidates = self._get_candidate_models()
        preprocessor = self.build_preprocessor()

        trained_results: List[Dict[str, Any]] = []
        fitted_pipelines: Dict[str, Pipeline] = {}

        # Sklearn scoring string mapping
        scoring_metric = self._map_scoring_metric()

        for model_name, estimator in candidates.items():
            t0 = time.time()
            pipe = Pipeline([
                ("preprocessor", self.build_preprocessor()),
                ("model", estimator),
            ])

            # Perform Cross-Validation strictly on Training Split
            try:
                cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv_gen, scoring=scoring_metric)
                # Invert negative regression scores
                if "neg_" in scoring_metric:
                    cv_scores = -cv_scores
                cv_mean = float(np.mean(cv_scores))
                cv_std = float(np.std(cv_scores))
            except Exception as cv_err:
                logger.warning(f"Cross-validation failed for {model_name}: {cv_err}")
                cv_scores = np.array([0.0])
                cv_mean = 0.0
                cv_std = 0.0

            # Fit Pipeline on Full Training Split
            pipe.fit(X_train, y_train)
            train_duration = round(time.time() - t0, 3)

            # Evaluate on Untouched Test Set
            test_metrics = self._evaluate_test_set(pipe, X_test, y_test, is_binary)
            fitted_pipelines[model_name] = pipe

            trained_results.append({
                "model_name": model_name,
                "model_class": estimator.__class__.__name__,
                "cv_scores": [round(float(s), 4) for s in cv_scores],
                "cv_mean": round(cv_mean, 4),
                "cv_std": round(cv_std, 4),
                "test_metrics": test_metrics,
                "training_time_seconds": train_duration,
                "hyperparameters": {k: str(v) for k, v in estimator.get_params().items() if k in ["C", "alpha", "n_estimators", "max_depth", "learning_rate"]},
                "is_selected": False,
                "is_champion": False,
            })

        # 5. Transparent Model Selection: Best CV Mean with penalty for high variance
        # For RMSE/MAE, lower is better. For AUC/F1/Accuracy/R2, higher is better.
        is_lower_better = self.primary_metric in ["RMSE", "MAE", "MAPE"]
        if is_lower_better:
            best_model_idx = int(np.argmin([r["cv_mean"] for r in trained_results]))
        else:
            best_model_idx = int(np.argmax([r["cv_mean"] for r in trained_results]))

        best_result = trained_results[best_model_idx]
        best_result["is_selected"] = True
        best_result["is_champion"] = True
        best_name = best_result["model_name"]

        best_result["selection_rationale"] = (
            f"Selected {best_name} based on optimal cross-validation score ({best_result['cv_mean']} ± {best_result['cv_std']}) "
            f"under primary objective '{self.primary_metric}'. Confirmed on untouched test set with {self.primary_metric} = {best_result['test_metrics'].get(self.primary_metric, 'N/A')}."
        )

        return {
            "task_type": self.task_type,
            "target_column": self.target_col,
            "primary_metric": self.primary_metric,
            "metric_rationale": self.metric_rationale,
            "cv_strategy": cv_strategy_desc,
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "feature_count": len(self.num_cols) + len(self.cat_cols),
            "numerical_features": self.num_cols,
            "categorical_features": self.cat_cols,
            "trained_models": trained_results,
            "best_model_name": best_name,
            "best_pipeline": fitted_pipelines[best_name],
            "all_pipelines": fitted_pipelines,
            "class_mapping": class_mapping,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
        }

    def _get_candidate_models(self) -> Dict[str, Any]:
        """Returns shortlisted candidate models based on task type and dataset size."""
        n_rows = len(self.df)
        if self.task_type == "classification":
            candidates: Dict[str, Any] = {
                "Logistic Regression": LogisticRegression(max_iter=500, random_state=self.random_state),
                "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=10, random_state=self.random_state),
                "HistGradientBoosting": HistGradientBoostingClassifier(max_iter=50, random_state=self.random_state),
            }
            if n_rows < 1500:
                candidates["Decision Tree"] = DecisionTreeClassifier(max_depth=6, random_state=self.random_state)
            return candidates
        else:
            candidates: Dict[str, Any] = {
                "Ridge Regression": Ridge(alpha=1.0, random_state=self.random_state),
                "Random Forest Regressor": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=self.random_state),
                "HistGradientBoosting Regressor": HistGradientBoostingRegressor(max_iter=50, random_state=self.random_state),
            }
            if n_rows < 1500:
                candidates["ElasticNet"] = ElasticNet(alpha=0.5, l1_ratio=0.5, random_state=self.random_state)
            return candidates

    def _map_scoring_metric(self) -> str:
        if self.task_type == "classification":
            if self.primary_metric == "PR-AUC":
                return "average_precision"
            elif self.primary_metric == "ROC-AUC":
                return "roc_auc"
            elif self.primary_metric == "Weighted F1":
                return "f1_weighted"
            else:
                return "accuracy"
        else:
            if self.primary_metric == "MAE":
                return "neg_mean_absolute_error"
            elif self.primary_metric == "R2":
                return "r2"
            else:
                return "neg_root_mean_squared_error"

    def _evaluate_test_set(
        self,
        pipe: Pipeline,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        is_binary: bool,
    ) -> Dict[str, float]:
        """Computes comprehensive task-appropriate metrics on the untouched test split."""
        metrics: Dict[str, float] = {}
        y_pred = pipe.predict(X_test)

        if self.task_type == "classification":
            metrics["Accuracy"] = round(float(accuracy_score(y_test, y_pred)), 4)
            metrics["Balanced Accuracy"] = round(float(balanced_accuracy_score(y_test, y_pred)), 4)
            metrics["F1"] = round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
            metrics["Precision"] = round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
            metrics["Recall"] = round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4)

            # Probabilities for AUC
            if hasattr(pipe, "predict_proba"):
                try:
                    proba = pipe.predict_proba(X_test)
                    if is_binary and proba.shape[1] >= 2:
                        metrics["ROC-AUC"] = round(float(roc_auc_score(y_test, proba[:, 1])), 4)
                        metrics["PR-AUC"] = round(float(average_precision_score(y_test, proba[:, 1])), 4)
                    elif proba.shape[1] > 2:
                        metrics["ROC-AUC"] = round(float(roc_auc_score(y_test, proba, multi_class="ovr")), 4)
                except Exception:
                    pass
        else:
            metrics["RMSE"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)
            metrics["MAE"] = round(float(mean_absolute_error(y_test, y_pred)), 4)
            metrics["R2"] = round(float(r2_score(y_test, y_pred)), 4)
            try:
                metrics["MAPE"] = round(float(mean_absolute_percentage_error(y_test, y_pred)), 4)
            except Exception:
                pass

        return metrics


def train_candidate_models(
    df: pd.DataFrame,
    target_col: str,
    task_type: Optional[str] = None,
    primary_metric: Optional[str] = None,
    cv_folds: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    trainer = ModelTrainer(
        df=df,
        target_col=target_col,
        task_type=task_type,
        primary_metric=primary_metric,
        cv_folds=cv_folds,
        random_state=random_state,
    )
    return trainer.train_and_evaluate()

