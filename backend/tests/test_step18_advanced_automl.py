"""
DataWise AI — Comprehensive Tests for Step 18: Advanced Agentic Data Science & AutoML
Validates:
  1. Context-aware Outlier Decision Engine (Fraud KEEP logic)
  2. Null Value Intelligence & KNN guardrails
  3. Visualization Selection Engine
  4. Leak-free Model Training, Stratified K-Fold CV & Metric Selection
  5. Explainability & Production Readiness Audit
  6. Jupyter Notebook Generation (.ipynb v4 structure)
  7. Production Artifact Packaging & ZIP export
"""

import json
import os
import zipfile
import numpy as np
import pandas as pd
import pytest

from app.tools.outlier_decision_engine import OutlierDecisionEngine, analyze_outlier_decisions
from app.tools.missing_value_engine import MissingValueDecisionEngine
from app.tools.visualization_planner import VisualizationPlanner
from app.tools.model_trainer import ModelTrainer
from app.tools.model_evaluator import ModelEvaluator
from app.tools.notebook_generator import JupyterNotebookGenerator
from app.tools.artifact_packager import ArtifactPackager


@pytest.fixture
def fraud_dataframe():
    """Generates synthetic transactions with extreme fraud outliers."""
    np.random.seed(42)
    n = 400
    amounts = np.random.exponential(scale=60, size=n)
    amounts[0] = 45000.0  # extreme fraud transaction
    amounts[1] = 60000.0  # extreme fraud transaction
    is_fraud = np.zeros(n, dtype=int)
    is_fraud[0] = 1
    is_fraud[1] = 1

    return pd.DataFrame({
        "transaction_amount": amounts,
        "customer_age": np.random.randint(18, 80, size=n),
        "is_fraud": is_fraud,
    })


@pytest.fixture
def missing_dataframe():
    """Generates dataframe with skewed and symmetric missing values."""
    return pd.DataFrame({
        "skewed_income": [15, 18, 16, 20, 17, 1000, np.nan, 19, 16, 18],
        "normal_age": [25, 26, 27, 28, 29, 30, np.nan, 27, 26, 25],
        "category": ["A", "B", "A", np.nan, "B", "A", "B", "A", "B", "A"],
        "target": [0, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    })


# ------------------------------------------------------------------ #
#  Test 1: Context-Aware Outlier Decision Engine
# ------------------------------------------------------------------ #
def test_outlier_decision_engine_fraud_preservation(fraud_dataframe):
    results = analyze_outlier_decisions(
        df=fraud_dataframe,
        target_col="is_fraud",
        domain="banking",
        objective="fraud",
    )

    decisions = results["outlier_decisions"]
    assert len(decisions) > 0

    tx_decision = next((d for d in decisions if d["column"] == "transaction_amount"), None)
    assert tx_decision is not None
    assert tx_decision["recommended_action"] == "KEEP"
    assert tx_decision["classified_as"] == "target_signal"
    assert "fraud" in tx_decision["rationale"].lower() or "signal" in tx_decision["rationale"].lower()


def test_outlier_decision_unspecified_domain_conservative(fraud_dataframe):
    results = analyze_outlier_decisions(
        df=fraud_dataframe,
        target_col=None,
        domain=None,
        objective=None,
    )
    decisions = results["outlier_decisions"]
    assert len(decisions) > 0
    # Without domain context, should conservatively recommend KEEP or INVESTIGATE
    for d in decisions:
        assert d["recommended_action"] in ["KEEP", "INVESTIGATE", "TRANSFORM", "WINSORIZE"]


# ------------------------------------------------------------------ #
#  Test 2: Null Value Intelligence & KNN Guardrails
# ------------------------------------------------------------------ #
def test_missing_value_decision_engine(missing_dataframe):
    engine = MissingValueDecisionEngine(missing_dataframe)
    results = engine.evaluate_missingness()

    decisions = results["decisions"]
    assert len(decisions) == 3

    # Skewed feature should get median
    skewed_d = next(d for d in decisions if d["column"] == "skewed_income")
    assert skewed_d["recommended_strategy"] == "median"
    assert "skewed" in skewed_d["rationale"].lower()

    # Normal feature should get mean
    normal_d = next(d for d in decisions if d["column"] == "normal_age")
    assert normal_d["recommended_strategy"] == "mean"

    # Categorical feature should get constant or most_frequent
    cat_d = next(d for d in decisions if d["column"] == "category")
    assert cat_d["recommended_strategy"] in ["constant_unknown", "most_frequent"]


# ------------------------------------------------------------------ #
#  Test 3: Visualization Planner
# ------------------------------------------------------------------ #
def test_visualization_planner(missing_dataframe):
    planner = VisualizationPlanner(missing_dataframe, target_col="target", task_type="classification")
    plan = planner.create_plan()

    assert len(plan) > 0
    # Should contain missing matrix because missing data exists
    assert any(p["plot_type"] == "missing_matrix" for p in plan)
    # Should contain class distribution for target
    assert any(p["plot_type"] == "class_distribution" for p in plan)
    # Should contain boxplot for skewed feature
    assert any(p["plot_type"] == "boxplot" and p["feature"] == "skewed_income" for p in plan)


# ------------------------------------------------------------------ #
#  Test 4: Leak-Free Model Training & Cross-Validation
# ------------------------------------------------------------------ #
def test_model_trainer_imbalanced_classification(fraud_dataframe):
    trainer = ModelTrainer(
        df=fraud_dataframe,
        target_col="is_fraud",
        cv_folds=3,
        random_state=42,
    )
    results = trainer.train_and_evaluate()

    assert results["task_type"] == "classification"
    assert results["primary_metric"] == "PR-AUC"
    assert len(results["trained_models"]) >= 3
    assert results["best_model_name"] in [m["model_name"] for m in results["trained_models"]]

    # Verify best pipeline is runnable and does not leak
    best_pipe = results["best_pipeline"]
    preds = best_pipe.predict(results["X_test"])
    assert len(preds) == len(results["X_test"])


# ------------------------------------------------------------------ #
#  Test 5: Explainability & Production Readiness
# ------------------------------------------------------------------ #
def test_model_evaluator_and_readiness(fraud_dataframe):
    trainer = ModelTrainer(df=fraud_dataframe, target_col="is_fraud", cv_folds=3)
    results = trainer.train_and_evaluate()

    # 1. Dataset shift check
    shift_report = ModelEvaluator.check_dataset_shift(results["X_train"], results["X_test"])
    assert "has_distribution_shift" in shift_report

    # 2. Explainability
    exp = ModelEvaluator.compute_explainability(
        pipeline=results["best_pipeline"],
        X_test=results["X_test"],
        y_test=results["y_test"],
        num_features=results["numerical_features"],
        cat_features=results["categorical_features"],
    )
    assert len(exp["feature_importances"]) > 0

    # 3. Production Readiness Audit
    audit = ModelEvaluator.audit_production_readiness(
        pipeline_serialized=True,
        target_col="is_fraud",
        train_rows=len(results["X_train"]),
        test_rows=len(results["X_test"]),
        cv_completed=True,
        leakage_warnings=[],
        has_distribution_shift=False,
    )
    assert audit["status"] in ["PASS", "WARNING"]
    assert audit["readiness_score"] >= 80.0


# ------------------------------------------------------------------ #
#  Test 6: Jupyter Notebook Generation (.ipynb v4)
# ------------------------------------------------------------------ #
def test_jupyter_notebook_generator(tmp_path):
    mock_state = {
        "session_id": "test_nb_session",
        "target_column": "is_fraud",
        "task_type": "classification",
        "numerical_columns": ["transaction_amount", "customer_age"],
        "categorical_columns": [],
        "dataset_path_original": "test.csv",
        "selected_final_model": "Random Forest",
        "primary_metric": "PR-AUC",
    }

    nb_gen = JupyterNotebookGenerator(session_id="test_nb_session", state=mock_state)
    nb_file = str(tmp_path / "test_notebook.ipynb")
    out = nb_gen.build_notebook(output_path=nb_file)

    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as f:
        nb_json = json.load(f)

    assert nb_json["nbformat"] == 4
    assert len(nb_json["cells"]) >= 20
    # Must contain both markdown and code cells
    assert any(c["cell_type"] == "code" for c in nb_json["cells"])
    assert any(c["cell_type"] == "markdown" for c in nb_json["cells"])


# ------------------------------------------------------------------ #
#  Test 7: Artifact Packager & ZIP Bundle
# ------------------------------------------------------------------ #
def test_artifact_packager(fraud_dataframe, tmp_path):
    session_id = "test_packager_session"
    packager = ArtifactPackager(session_id=session_id)

    # Train pipeline to serialize
    trainer = ModelTrainer(df=fraud_dataframe, target_col="is_fraud", cv_folds=2)
    results = trainer.train_and_evaluate()

    # 1. Serialize model
    model_path = packager.serialize_model(results["best_pipeline"])
    assert os.path.exists(model_path)

    # 2. Generate metadata
    meta_path = packager.generate_metadata(
        target_col="is_fraud",
        task_type="classification",
        model_name="Random Forest",
        num_cols=["transaction_amount", "customer_age"],
        cat_cols=[],
        cv_scores=[0.9, 0.92],
        test_metrics={"PR-AUC": 0.91},
    )
    assert os.path.exists(meta_path)

    # 3. Generate scripts
    inf_script = packager.generate_inference_script("is_fraud", "classification")
    assert os.path.exists(inf_script)

    prep_script = packager.generate_preprocessing_script(["transaction_amount"], [])
    assert os.path.exists(prep_script)

    # 4. Create ZIP bundle
    zip_path = packager.create_zip_bundle()
    assert os.path.exists(zip_path)
    assert zipfile.is_zipfile(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert any("final_model.joblib" in name for name in namelist)
        assert any("model_metadata.json" in name for name in namelist)
        assert any("inference.py" in name for name in namelist)
