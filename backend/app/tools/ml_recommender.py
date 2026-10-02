"""
DataWise AI — ML Recommendation Engine

Analyses dataset characteristics and recommends appropriate ML algorithms
with detailed rationale, pros/cons, hyperparameter starting points,
and evaluation strategy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ #
#  Model catalogue
# ------------------------------------------------------------------ #

CLASSIFICATION_MODELS = [
    {
        "model_name": "Random Forest Classifier",
        "model_class": "sklearn.ensemble.RandomForestClassifier",
        "tags": ["tabular", "robust", "nonlinear", "feature_importance"],
        "pros": [
            "Robust to outliers and missing value proxies",
            "Built-in feature importance",
            "Handles high-dimensional data well",
            "No feature scaling required",
        ],
        "cons": [
            "Can be slow on very large datasets",
            "Less interpretable than linear models",
            "Memory-intensive for many trees",
        ],
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": None,
            "min_samples_split": 2,
            "class_weight": "balanced",
        },
        "evaluation_metrics": ["accuracy", "f1_weighted", "roc_auc", "precision_recall_auc"],
        "suitable_for": ["binary", "multiclass", "imbalanced"],
    },
    {
        "model_name": "Gradient Boosting (XGBoost / LightGBM)",
        "model_class": "xgboost.XGBClassifier",
        "tags": ["tabular", "state_of_art", "nonlinear", "kaggle"],
        "pros": [
            "State-of-the-art performance on tabular data",
            "Handles missing values natively",
            "Built-in regularization",
            "Fast with GPU support",
        ],
        "cons": [
            "Requires hyperparameter tuning",
            "Prone to overfitting on small datasets",
            "Less interpretable",
        ],
        "hyperparameters": {
            "n_estimators": 200,
            "learning_rate": 0.1,
            "max_depth": 6,
            "scale_pos_weight": "auto_for_imbalance",
        },
        "evaluation_metrics": ["f1_weighted", "roc_auc", "log_loss"],
        "suitable_for": ["binary", "multiclass", "imbalanced", "large_dataset"],
    },
    {
        "model_name": "Logistic Regression",
        "model_class": "sklearn.linear_model.LogisticRegression",
        "tags": ["linear", "interpretable", "fast"],
        "pros": [
            "Highly interpretable coefficients",
            "Fast training and inference",
            "Good baseline model",
            "Probabilistic output",
        ],
        "cons": [
            "Assumes linear decision boundary",
            "Sensitive to multicollinearity",
            "Requires feature scaling",
        ],
        "hyperparameters": {
            "C": 1.0,
            "solver": "lbfgs",
            "max_iter": 1000,
            "class_weight": "balanced",
        },
        "evaluation_metrics": ["accuracy", "f1_weighted", "roc_auc"],
        "suitable_for": ["binary", "multiclass", "linear_separable"],
    },
    {
        "model_name": "Support Vector Machine (SVM)",
        "model_class": "sklearn.svm.SVC",
        "tags": ["kernel", "small_dataset", "high_dimensional"],
        "pros": [
            "Effective in high-dimensional spaces",
            "Kernel trick handles non-linear boundaries",
            "Memory efficient",
        ],
        "cons": [
            "Slow on large datasets (O(n³))",
            "Requires feature scaling",
            "Difficult to interpret",
        ],
        "hyperparameters": {
            "C": 1.0,
            "kernel": "rbf",
            "probability": True,
            "class_weight": "balanced",
        },
        "evaluation_metrics": ["accuracy", "f1_weighted", "roc_auc"],
        "suitable_for": ["binary", "small_dataset", "high_dimensional"],
    },
]

REGRESSION_MODELS = [
    {
        "model_name": "Random Forest Regressor",
        "model_class": "sklearn.ensemble.RandomForestRegressor",
        "tags": ["tabular", "robust", "nonlinear"],
        "pros": [
            "Robust to outliers",
            "Captures non-linear relationships",
            "No scaling required",
            "Built-in feature importance",
        ],
        "cons": ["Not extrapolation-friendly", "Memory intensive"],
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": None,
            "min_samples_split": 2,
        },
        "evaluation_metrics": ["rmse", "mae", "r2", "mape"],
        "suitable_for": ["nonlinear", "tabular", "robust"],
    },
    {
        "model_name": "Gradient Boosting Regressor (XGBoost)",
        "model_class": "xgboost.XGBRegressor",
        "tags": ["tabular", "state_of_art", "nonlinear"],
        "pros": [
            "Best-in-class tabular performance",
            "Handles missing values natively",
            "Feature importance",
        ],
        "cons": ["Needs tuning", "Can overfit small datasets"],
        "hyperparameters": {
            "n_estimators": 200,
            "learning_rate": 0.05,
            "max_depth": 6,
            "subsample": 0.8,
        },
        "evaluation_metrics": ["rmse", "mae", "r2"],
        "suitable_for": ["nonlinear", "large_dataset", "tabular"],
    },
    {
        "model_name": "Ridge Regression",
        "model_class": "sklearn.linear_model.Ridge",
        "tags": ["linear", "regularized", "interpretable"],
        "pros": [
            "Handles multicollinearity well",
            "Fast and interpretable",
            "Good baseline",
        ],
        "cons": ["Assumes linear relationship", "Sensitive to outliers"],
        "hyperparameters": {"alpha": 1.0},
        "evaluation_metrics": ["rmse", "r2", "mae"],
        "suitable_for": ["linear", "multicollinear", "small_dataset"],
    },
    {
        "model_name": "ElasticNet",
        "model_class": "sklearn.linear_model.ElasticNet",
        "tags": ["linear", "regularized", "feature_selection"],
        "pros": [
            "Combines L1 (feature selection) and L2 (grouping effect)",
            "Sparse model output",
        ],
        "cons": ["Linear assumption", "Needs scaling"],
        "hyperparameters": {"alpha": 0.1, "l1_ratio": 0.5},
        "evaluation_metrics": ["rmse", "r2"],
        "suitable_for": ["linear", "high_dimensional", "sparse"],
    },
]

CLUSTERING_MODELS = [
    {
        "model_name": "K-Means Clustering",
        "model_class": "sklearn.cluster.KMeans",
        "tags": ["clustering", "unsupervised", "fast"],
        "pros": ["Simple and fast", "Scales to large datasets", "Easy to interpret"],
        "cons": ["Must specify K", "Assumes spherical clusters", "Sensitive to outliers"],
        "hyperparameters": {"n_clusters": 3, "init": "k-means++", "n_init": 10},
        "evaluation_metrics": ["silhouette_score", "davies_bouldin_score", "inertia"],
        "suitable_for": ["clustering", "spherical_clusters"],
    },
    {
        "model_name": "DBSCAN",
        "model_class": "sklearn.cluster.DBSCAN",
        "tags": ["clustering", "density_based", "anomaly"],
        "pros": ["No K required", "Detects noise/anomalies", "Non-spherical clusters"],
        "cons": ["Sensitive to eps and min_samples", "Slow on large datasets"],
        "hyperparameters": {"eps": 0.5, "min_samples": 5},
        "evaluation_metrics": ["silhouette_score", "noise_ratio"],
        "suitable_for": ["clustering", "anomaly_detection", "non_spherical"],
    },
]


# ------------------------------------------------------------------ #
#  ML Readiness Scorer
# ------------------------------------------------------------------ #

def compute_ml_readiness(
    row_count: int,
    col_count: int,
    missing_pct_avg: float,
    high_severity_missing: int,
    duplicate_pct: float,
    outlier_severity: str,
    leakage_warnings: int,
    has_target: bool,
) -> Dict[str, Any]:
    """Score ML readiness on a 0–100 scale."""
    score = 100.0

    # Penalise small datasets
    if row_count < 100:
        score -= 30
    elif row_count < 500:
        score -= 15
    elif row_count < 1000:
        score -= 5

    # Penalise missing values
    score -= min(25, missing_pct_avg * 2)

    # Critical missing columns
    score -= high_severity_missing * 8

    # Duplicates
    score -= min(10, duplicate_pct * 0.5)

    # Outlier severity
    penalty_map = {"none": 0, "mild": 2, "moderate": 5, "severe": 12}
    score -= penalty_map.get(outlier_severity, 0)

    # Leakage warnings
    score -= leakage_warnings * 10

    # No target defined
    if not has_target:
        score -= 15

    score = max(0.0, min(100.0, score))

    if score >= 80:
        level = "READY_FOR_BASELINE"
        message = "Dataset is ML-ready. A baseline model can be trained now."
    elif score >= 50:
        level = "NEEDS_PREPROCESSING"
        message = "Dataset needs preprocessing before ML training. Follow the recommendations."
    else:
        level = "NOT_READY"
        message = "Dataset has critical issues that must be resolved before training any model."

    return {
        "score": round(score, 1),
        "level": level,
        "message": message,
    }


# ------------------------------------------------------------------ #
#  ML Recommender
# ------------------------------------------------------------------ #

class MLRecommender:
    """Recommends ML algorithms based on dataset and task characteristics."""

    def __init__(
        self,
        task_type: str = "classification",
        row_count: int = 0,
        col_count: int = 0,
        is_imbalanced: bool = False,
        has_high_cardinality: bool = False,
        is_high_dimensional: bool = False,
        missing_pct_avg: float = 0.0,
        high_severity_missing: int = 0,
        duplicate_pct: float = 0.0,
        outlier_severity: str = "none",
        leakage_warnings: int = 0,
        has_target: bool = True,
        target_col: Any = None,
        **kwargs: Any,
    ) -> None:
        self.task_type = task_type
        self.row_count = row_count
        self.col_count = col_count
        self.target_col = target_col
        self.is_imbalanced = is_imbalanced
        self.has_high_cardinality = has_high_cardinality
        self.is_high_dimensional = is_high_dimensional
        self.missing_pct_avg = missing_pct_avg
        self.high_severity_missing = high_severity_missing
        self.duplicate_pct = duplicate_pct
        self.outlier_severity = outlier_severity
        self.leakage_warnings = leakage_warnings
        self.has_target = has_target

    def recommend(self) -> Dict[str, Any]:
        readiness = compute_ml_readiness(
            self.row_count,
            self.col_count,
            self.missing_pct_avg,
            self.high_severity_missing,
            self.duplicate_pct,
            self.outlier_severity,
            self.leakage_warnings,
            self.has_target,
        )

        recommendations = self._select_models()
        evaluation_plan = self._evaluation_plan(recommendations)

        return {
            "task_type": self.task_type,
            "ml_readiness": readiness,
            "recommendations": recommendations,
            "evaluation_plan": evaluation_plan,
            "roadmap": self._build_roadmap(readiness, recommendations),
        }

    def _select_models(self) -> List[Dict[str, Any]]:
        if self.task_type == "classification":
            catalogue = CLASSIFICATION_MODELS
        elif self.task_type == "regression":
            catalogue = REGRESSION_MODELS
        elif self.task_type == "clustering":
            return CLUSTERING_MODELS[:2]
        else:
            catalogue = REGRESSION_MODELS  # time_series → regression baseline

        scored = []
        for m in catalogue:
            s = 0
            tags = m.get("suitable_for", [])
            if self.is_imbalanced and "imbalanced" in tags:
                s += 2
            if self.row_count > 10000 and "large_dataset" in tags:
                s += 2
            if self.row_count < 1000 and "small_dataset" in tags:
                s += 2
            if self.is_high_dimensional and "high_dimensional" in tags:
                s += 2
            # Gradient boosting generally wins on tabular data
            if "state_of_art" in m.get("tags", []):
                s += 1
            scored.append((s, m))

        scored = sorted(scored, key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:3]]

    def _evaluation_plan(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_metrics: List[str] = []
        for m in models:
            all_metrics.extend(m.get("evaluation_metrics", []))
        unique_metrics = list(dict.fromkeys(all_metrics))

        return {
            "cross_validation": "5-fold StratifiedKFold" if self.task_type == "classification" else "5-fold KFold",
            "primary_metric": unique_metrics[0] if unique_metrics else "accuracy",
            "secondary_metrics": unique_metrics[1:4],
            "train_test_split": "80% train / 20% test",
            "notes": (
                "Use StratifiedKFold for imbalanced datasets. "
                "Always evaluate on held-out test set after hyperparameter tuning."
                if self.is_imbalanced else
                "Standard 5-fold cross-validation is appropriate for this dataset."
            ),
        }

    def _build_roadmap(
        self, readiness: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        model_names = [m["model_name"] for m in models[:3]]
        steps = [
            {
                "step": 1,
                "name": "Data Preprocessing",
                "description": "Apply the generated sklearn Pipeline to clean and transform the dataset.",
                "status": "ready",
            },
            {
                "step": 2,
                "name": "Baseline Model Training",
                "description": f"Train {model_names[0] if model_names else 'a simple model'} as baseline.",
                "status": "pending",
            },
            {
                "step": 3,
                "name": "Cross-Validation",
                "description": f"Evaluate using {readiness.get('level', 'CV')} strategy across 5 folds.",
                "status": "pending",
            },
            {
                "step": 4,
                "name": "Model Comparison",
                "description": f"Compare {', '.join(model_names)} on validation set.",
                "status": "pending",
            },
            {
                "step": 5,
                "name": "Hyperparameter Tuning",
                "description": "Use RandomizedSearchCV or Optuna to tune the best model.",
                "status": "pending",
            },
            {
                "step": 6,
                "name": "Final Evaluation",
                "description": "Evaluate best model on held-out test set. Generate confusion matrix / residuals.",
                "status": "pending",
            },
            {
                "step": 7,
                "name": "Model Export",
                "description": "Save trained pipeline with joblib for deployment.",
                "status": "pending",
            },
        ]
        return steps


def recommend_algorithms(
    task_type: Any = "classification",
    row_count: int = 1000,
    col_count: int = 10,
    **kwargs: Any,
) -> Dict[str, Any]:
    if isinstance(task_type, pd.DataFrame):
        df = task_type
        row_count = len(df)
        col_count = len(df.columns)
        task_type = kwargs.get("problem_type") or kwargs.get("task_type") or "classification"

    recommender = MLRecommender(
        task_type=task_type,
        row_count=row_count,
        col_count=col_count,
        **kwargs,
    )
    res = recommender.recommend()
    if "candidate_models" not in res:
        res["candidate_models"] = res.get("recommendations", [])
    return res


def get_algorithm_suitability(algorithm_name: str, task_type: str = "classification") -> Dict[str, Any]:
    catalogue = CLASSIFICATION_MODELS if task_type == "classification" else REGRESSION_MODELS
    for m in catalogue:
        if algorithm_name.lower() in m["model_name"].lower():
            return m
    return {
        "model_name": algorithm_name,
        "suitable_for": [task_type],
        "pros": ["General purpose"],
        "cons": ["Requires tuning"],
    }

