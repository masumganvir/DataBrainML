"""
DataWise AI — Comprehensive Test Suite for Master Tools Directory (Section 4)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from tools.ingestion import load_csv, load_json, validate_file
from tools.profiling import extract_schema, compute_column_statistics, analyze_cardinality, profile_dataset
from tools.data_quality import audit_data_quality, detect_missing_values, detect_duplicates
from tools.outliers import analyze_all_outliers, detect_outliers_iqr
from tools.visualization import generate_distribution_spec, generate_categorical_spec, generate_correlation_matrix_spec
from tools.preprocessing import split_dataset, build_column_transformer
from tools.feature_engineering import recommend_and_engineer_features
from tools.feature_selection import run_feature_selection_suite
from tools.leakage import audit_dataset_leakage, detect_target_leakage
from tools.models import get_candidate_models
from tools.evaluation import evaluate_classification, evaluate_regression, run_cross_validation
from tools.tuning import run_random_search
from tools.notebook import NotebookGenerator
from tools.reporting import generate_html_report, generate_markdown_report
from tools.serialization import save_pipeline, load_pipeline, generate_model_metadata


@pytest.fixture
def sample_dataset(tmp_path):
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "age": np.random.randint(18, 70, size=n),
        "income": np.random.normal(50000, 15000, size=n),
        "department": np.random.choice(["Sales", "Engineering", "HR"], size=n),
        "target": np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
    })
    # Add a missing value and an outlier
    df.loc[0, "income"] = np.nan
    df.loc[1, "income"] = 500000.0  # outlier

    csv_path = tmp_path / "sample.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path), df


def test_ingestion_tools(sample_dataset, tmp_path):
    csv_path, _ = sample_dataset
    df, meta = load_csv(csv_path)
    assert len(df) == 100
    assert meta["format"] == "csv"

    val_res = validate_file(csv_path)
    assert val_res["valid"] is True


def test_profiling_tools(sample_dataset):
    _, df = sample_dataset
    profile = profile_dataset(df)
    assert profile["summary"]["total_rows"] == 100
    assert "income" in profile["statistics"]
    assert profile["statistics"]["income"]["missing_count"] == 1


def test_data_quality_tools(sample_dataset):
    _, df = sample_dataset
    audit = audit_data_quality(df)
    assert audit["quality_score"] > 50.0
    assert audit["missing_analysis"]["missing_columns_count"] >= 1


def test_outlier_intelligence(sample_dataset):
    _, df = sample_dataset
    outliers = analyze_all_outliers(df, target_column="target")
    assert "income" in outliers["features"]
    assert outliers["features"]["income"]["iqr"]["outlier_count"] >= 1


def test_visualization_tools(sample_dataset):
    _, df = sample_dataset
    dist_spec = generate_distribution_spec(df["age"])
    assert dist_spec["plot_type"] == "histogram_kde"

    cat_spec = generate_categorical_spec(df["department"])
    assert cat_spec["plot_type"] == "categorical_bar"

    corr_spec = generate_correlation_matrix_spec(df)
    assert corr_spec["plot_type"] == "correlation_heatmap"


def test_preprocessing_and_pipeline(sample_dataset):
    _, df = sample_dataset
    X_train, X_test, y_train, y_test = split_dataset(df, target_column="target", test_size=0.2)
    assert len(X_train) == 80
    assert len(X_test) == 20

    transformer = build_column_transformer(["age", "income"], ["department"])
    transformer.fit(X_train)
    transformed = transformer.transform(X_train)
    assert transformed.shape[0] == 80


def test_feature_engineering_and_selection(sample_dataset):
    _, df = sample_dataset
    fe = recommend_and_engineer_features(df, target_column="target")
    assert fe["recommendation_count"] >= 1

    fs = run_feature_selection_suite(df.dropna(), target_column="target", task_type="classification")
    assert len(fs["recommended_features"]) >= 1


def test_data_leakage_detection(sample_dataset):
    _, df = sample_dataset
    # Add leak column
    df_leak = df.copy()
    df_leak["leak_col"] = df_leak["target"]

    leak_audit = audit_dataset_leakage(df_leak, target_column="target")
    assert leak_audit["has_leakage"] is True
    assert leak_audit["should_block_pipeline"] is True


def test_models_and_evaluation(sample_dataset):
    _, df = sample_dataset
    clean_df = df.dropna()
    X = clean_df[["age"]].values
    y = clean_df["target"].values

    models = get_candidate_models(task_type="classification", n_samples=len(clean_df))
    assert "RandomForest" in models

    rf = models["RandomForest"]
    cv_res = run_cross_validation(rf, X, y, cv=3)
    assert "mean_score" in cv_res

    rf.fit(X, y)
    y_pred = rf.predict(X)
    eval_res = evaluate_classification(y, y_pred)
    assert "accuracy" in eval_res


def test_notebook_and_reporting_and_serialization(sample_dataset, tmp_path):
    csv_path, _ = sample_dataset
    state = {
        "dataset_path": csv_path,
        "target_column": "target",
        "ml_task_type": "classification",
        "selected_final_model": "RandomForest",
    }

    # Notebook
    nb_path = tmp_path / "test_nb.ipynb"
    gen = NotebookGenerator(state)
    gen.generate(str(nb_path))
    assert nb_path.exists()
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_json = json.load(f)
    assert len(nb_json["cells"]) >= 35

    # Report
    html_report = generate_html_report(state)
    assert "DataWise AI Production Report" in html_report

    md_report = generate_markdown_report(state)
    assert "Executive Summary" in md_report

    # Serialization
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression()
    clf.fit([[1], [2], [3], [4]], [0, 0, 1, 1])

    mod_path = tmp_path / "model.joblib"
    save_pipeline(clf, str(mod_path))
    loaded = load_pipeline(str(mod_path))
    assert loaded.predict([[2]])[0] in (0, 1)

    meta = generate_model_metadata("LogisticRegression", "target", ["f1"], "classification", {"acc": 0.95})
    assert meta["model_name"] == "LogisticRegression"
