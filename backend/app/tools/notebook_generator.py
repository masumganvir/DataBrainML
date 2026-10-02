"""
DataWise AI — Jupyter Notebook Generator

Generates a fully executable 24-section Jupyter Notebook (.ipynb) conforming to
Section 28 and Section 29 specifications.
Features real executable Python cells, data loading, preprocessing pipelines,
cross-validation, model comparison, and serialization.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config.settings import get_settings

settings = get_settings()


class JupyterNotebookGenerator:
    """
    Builds a standards-compliant Jupyter Notebook (.ipynb v4) representing the complete
    Data Science & AutoML workflow.
    """

    def __init__(self, session_id: str, state: Dict[str, Any]):
        self.session_id = session_id
        self.state = state
        self.cells: List[Dict[str, Any]] = []

    def _add_markdown(self, markdown_text: str) -> None:
        lines = [line + "\n" for line in markdown_text.strip().split("\n")]
        if lines:
            lines[-1] = lines[-1].rstrip("\n")
        self.cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": lines,
        })

    def _add_code(self, code_text: str) -> None:
        lines = [line + "\n" for line in code_text.strip().split("\n")]
        if lines:
            lines[-1] = lines[-1].rstrip("\n")
        self.cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": lines,
        })

    def build_notebook(self, output_path: Optional[str] = None) -> str:
        """Constructs all 24 sections and saves the notebook."""
        target_col = self.state.get("target_column", "target")
        task_type = self.state.get("task_type", "classification")
        num_cols = self.state.get("numerical_columns", [])
        cat_cols = self.state.get("categorical_columns", [])
        dataset_path = self.state.get("dataset_path_original", "dataset.csv")
        selected_model = self.state.get("selected_final_model", "Random Forest")
        primary_metric = self.state.get("primary_metric", "Score")

        # 1. Project Title
        self._add_markdown(f"""# DataWise AI — Autonomous Machine Learning & Data Science Notebook
**Session ID:** `{self.session_id}`  
**Generated At:** `{datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}`  
**Objective:** End-to-end data preparation, exploratory data analysis, leak-free pipeline engineering, and candidate model evaluation.""")

        # 2. Dataset Description
        self._add_markdown(f"""## 1. Dataset Description & Objective
- **Target Feature:** `{target_col}`
- **Task Type:** `{task_type.capitalize()}`
- **Primary Optimization Metric:** `{primary_metric}`
- **Dataset Domain:** `{self.state.get('dataset_domain', 'General Data Science')}`
- **Prediction Objective:** `{self.state.get('prediction_objective', 'Supervised Prediction')}`""")

        # 3. Imports
        self._add_code("""import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Sklearn Preprocessing & Pipelines
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler

# Sklearn Estimators & Metrics
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error, r2_score

# Visual aesthetics
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
%matplotlib inline
""")

        # 4. Dataset Loading
        self._add_markdown("## 2. Dataset Loading")
        self._add_code(f"""# Load the primary dataset
dataset_path = r"{dataset_path}"
df = pd.read_csv(dataset_path)
print(f"Dataset successfully loaded. Dimensions: {{df.shape[0]:,}} rows x {{df.shape[1]:,}} columns")
df.head(5)""")

        # 5. Dataset Overview
        self._add_markdown("## 3. Dataset Overview & Schema Inspection")
        self._add_code("""print("--- Summary Info ---")
df.info()
print("\\n--- Numerical Feature Statistics ---")
df.describe().T""")

        # 6. Data Types
        self._add_markdown("## 4. Data Type Classification")
        self._add_code(f"""num_features = {num_cols}
cat_features = {cat_cols}
target = "{target_col}"

print(f"Identified {{len(num_features)}} Numerical Features: {{num_features}}")
print(f"Identified {{len(cat_features)}} Categorical Features: {{cat_features}}")
print(f"Target Feature: {{target}}")""")

        # 7. Missing-Value Analysis
        self._add_markdown("## 5. Missing Value Analysis & Intelligence")
        self._add_code("""null_counts = df.isna().sum()
null_pct = (null_counts / len(df)) * 100
missing_df = pd.DataFrame({'Missing Count': null_counts, 'Missing %': null_pct.round(2)})
missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values(by='Missing %', ascending=False)

if len(missing_df) > 0:
    print(missing_df)
else:
    print("No missing values detected across dataset columns.")""")

        # 8. Duplicate Analysis
        self._add_markdown("## 6. Duplicate Records Audit")
        self._add_code("""dup_count = df.duplicated().sum()
dup_pct = round((dup_count / len(df)) * 100, 2)
print(f"Exact Duplicate Rows: {dup_count:,} ({dup_pct}%)")
if dup_count > 0:
    print("Duplicate instances should be removed prior to model training to prevent train-test contamination.")""")

        # 9. Outlier Analysis
        self._add_markdown("""## 7. Context-Aware Outlier Analysis
Outliers are evaluated in relation to the target objective. Extreme values in anomaly/fraud contexts are retained to preserve critical signal.""")
        self._add_code("""for col in num_features[:4]:
    s = df[col].dropna()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = s[(s < lower_bound) | (s > upper_bound)]
    print(f"{col}: {len(outliers):,} outliers ({round(len(outliers)/len(s)*100, 2)}%) outside [{lower_bound:.2f}, {upper_bound:.2f}]")""")

        # 10. Distribution Analysis
        self._add_markdown("## 8. Continuous Feature Skewness & Kurtosis")
        self._add_code("""skew_vals = df[num_features].skew().round(2)
kurt_vals = df[num_features].kurt().round(2)
pd.DataFrame({'Skewness': skew_vals, 'Kurtosis': kurt_vals}).head(10)""")

        # 11. Visualizations
        self._add_markdown("## 9. Key Exploratory Visualizations")
        self._add_code("""fig, axes = plt.subplots(1, min(3, len(num_features)), figsize=(15, 4))
if not isinstance(axes, np.ndarray):
    axes = np.array([axes])

for i, col in enumerate(num_features[:3]):
    sns.histplot(df[col], kde=True, ax=axes[i], color='royalblue')
    axes[i].set_title(f'Distribution: {col}')
plt.tight_layout()
plt.show()""")

        # 12. Correlation Analysis
        self._add_markdown("## 10. Correlation Analysis")
        self._add_code("""if len(num_features) >= 2:
    plt.figure(figsize=(8, 6))
    corr = df[num_features].corr()
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Feature Correlation Matrix')
    plt.show()""")

        # 13. Feature Engineering
        self._add_markdown("## 11. Feature Engineering Foundations")
        self._add_code("""# Optional engineered interaction terms or log transformations
df_features = df.copy()
# Preserve pure features without leakage
print("Feature space ready for split.")""")

        # 14. Train/Test Separation (STRICT LEAKAGE PREVENTION)
        self._add_markdown("""## 12. Strict Train / Test Split (Leakage Prevention)
**CRITICAL:** The test set is partitioned immediately on raw features before any scalers, encoders, or imputers are fitted.""")
        self._add_code(f"""X = df.drop(columns=[target])
y = df[target]

# 80/20 train/test partition
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y if "{task_type}" == "classification" and y.nunique() <= 10 else None
)

print(f"X_train shape: {{X_train.shape}} | y_train shape: {{y_train.shape}}")
print(f"X_test shape:  {{X_test.shape}}  | y_test shape:  {{y_test.shape}}")""")

        # 15. ColumnTransformer Assembly
        self._add_markdown("## 13. Preprocessing ColumnTransformer")
        self._add_code("""num_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

cat_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

preprocessor = ColumnTransformer(transformers=[
    ('num', num_pipeline, num_features),
    ('cat', cat_pipeline, cat_features)
], remainder='drop')

print("ColumnTransformer constructed successfully.")""")

        # 16. Candidate Models Definition
        self._add_markdown("## 14. Candidate ML Models Setup")
        self._add_code(f"""task = "{task_type}"

if task == "classification":
    models = {{
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=42)
    }}
else:
    models = {{
        "Ridge Regression": Ridge(alpha=1.0, random_state=42),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42),
        "HistGradientBoosting Regressor": HistGradientBoostingRegressor(random_state=42)
    }}""")

        # 17. Cross-Validation
        self._add_markdown("## 15. K-Fold Cross-Validation on Training Split")
        self._add_code(f"""cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42) if task == "classification" else KFold(n_splits=5, shuffle=True, random_state=42)
scoring_metric = "average_precision" if "{primary_metric}" == "PR-AUC" else ("roc_auc" if "{primary_metric}" == "ROC-AUC" else "accuracy")

cv_results = {{}}
trained_pipelines = {{}}

for name, estimator in models.items():
    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('model', estimator)
    ])
    scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring=scoring_metric)
    pipe.fit(X_train, y_train)
    trained_pipelines[name] = pipe
    cv_results[name] = (scores.mean(), scores.std())
    print(f"{{name:<25}} | CV {{scoring_metric}}: {{scores.mean():.4f}} ± {{scores.std():.4f}}")""")

        # 18. Model Comparison
        self._add_markdown("## 16. Model Comparison Dashboard")
        self._add_code("""comparison_df = pd.DataFrame([
    {'Model': name, 'CV Mean': cv[0], 'CV Std': cv[1], 'Test Score': round(trained_pipelines[name].score(X_test, y_test), 4)}
    for name, cv in cv_results.items()
]).sort_values(by='CV Mean', ascending=False)

print(comparison_df.to_string(index=False))""")

        # 19. Final Model Selection
        self._add_markdown(f"## 17. Final Model Selection: `{selected_model}`")
        self._add_code(f"""best_model_name = "{selected_model}" if "{selected_model}" in trained_pipelines else comparison_df.iloc[0]['Model']
final_pipeline = trained_pipelines[best_model_name]
print(f"Selected Champion Pipeline: {{best_model_name}}")""")

        # 20. Hold-out Test Set Evaluation
        self._add_markdown("## 18. Hold-Out Test Set Evaluation")
        self._add_code(f"""y_pred = final_pipeline.predict(X_test)

if task == "classification":
    print("--- Classification Report ---")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("--- Confusion Matrix ---")
    print(confusion_matrix(y_test, y_pred))
else:
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"Test RMSE: {{rmse:.4f}}")
    print(f"Test R^2:  {{r2:.4f}}")""")

        # 21. Model Serialization (joblib)
        self._add_markdown("## 19. Final Model Serialization")
        self._add_code("""export_path = "final_model.joblib"
joblib.dump(final_pipeline, export_path)
print(f"Unified model pipeline successfully serialized to: {export_path}")
print("Pipeline is standalone and directly executable for production inference.")""")

        # 22. Inference Demonstration
        self._add_markdown("## 20. Production Inference Demonstration")
        self._add_code("""# Load and test artifact
loaded_model = joblib.load(export_path)
sample_unseen = X_test.iloc[:5]
sample_preds = loaded_model.predict(sample_unseen)
print("Input Sample Predictions:", sample_preds)""")

        # 23. Analytical Limitations
        self._add_markdown("""## 21. Model Limitations & Assumptions
1. **Covariate Drift:** Model performance is conditional on incoming data matching training feature distributions.
2. **Confounders:** Predictions represent statistical correlation, not causal intervention.
3. **Threshold Calibration:** Optimal classification decision threshold must be calibrated according to business cost matrices.""")

        # 24. Future Machine Learning Roadmap
        self._add_markdown("""## 22. Production ML Roadmap
- [x] Automated exploratory data analysis & schema typing
- [x] Leak-free ColumnTransformer pipeline assembly
- [x] K-Fold cross-validation & candidate comparison
- [ ] Integration of advanced gradient boosting (LightGBM, XGBoost)
- [ ] Real-time concept drift monitoring and automated retraining pipelines
- [ ] SHAP (SHapley Additive exPlanations) production attribution tracking
""")

        # Output path
        if not output_path:
            nb_dir = settings.artifacts_dir_path / self.session_id / "DataWise_Project" / "notebook"
            nb_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(nb_dir / f"dataset_analysis_{timestamp}.ipynb")

        notebook_dict = {
            "cells": self.cells,
            "metadata": {
                "language_info": {
                    "name": "python",
                    "version": "3.10",
                },
                "orig_nbformat": 4,
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notebook_dict, f, indent=1)

        logger.info(f"Executable Jupyter Notebook written to: {output_path}")
        return output_path
