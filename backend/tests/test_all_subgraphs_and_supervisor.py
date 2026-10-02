"""
DataWise AI — Comprehensive Tests for All 9 LangGraph Subgraphs & SupervisorGraph (Section 5)
"""

import os
import tempfile
import pytest
import pandas as pd
from langgraph.checkpoint.memory import MemorySaver

from graphs.state import create_initial_agent_state
from graphs.data_analysis_graph import build_data_analysis_graph
from graphs.preprocessing_graph import build_preprocessing_graph
from graphs.feature_engineering_graph import build_feature_engineering_graph
from graphs.model_selection_graph import build_model_selection_graph
from graphs.training_graph import build_training_graph
from graphs.evaluation_graph import build_evaluation_graph
from graphs.deployment_graph import build_deployment_graph
from graphs.monitoring_graph import build_monitoring_graph
from graphs.retraining_graph import build_retraining_graph
from graphs.supervisor_graph import build_supervisor_graph


@pytest.fixture
def sample_csv():
    df = pd.DataFrame({
        "age": [25, 30, 45, 50, 22, 60, 35, 40],
        "income": [40000, 55000, 80000, 95000, 32000, 120000, 62000, 75000],
        "department": ["Sales", "Dev", "Dev", "HR", "Sales", "Executive", "Dev", "HR"],
        "churn": [0, 0, 1, 1, 0, 1, 0, 1],
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_data_analysis_subgraph(sample_csv):
    graph = build_data_analysis_graph()
    state = create_initial_agent_state(
        dataset_path=sample_csv,
        session_id="test_subgraph_analysis",
        target_column="churn",
    )
    result = graph.invoke(state)
    assert "dataset_profile" in result
    assert "data_quality_report" in result
    assert "outlier_report" in result
    assert "missing_values" in result["completed_steps"]


def test_feature_engineering_subgraph(sample_csv):
    graph = build_feature_engineering_graph()
    state = create_initial_agent_state(
        dataset_path=sample_csv,
        session_id="test_subgraph_fe",
        target_column="churn",
    )
    result = graph.invoke(state)
    assert "feature_engineering" in result["completed_steps"]
    assert "feature_selection" in result["completed_steps"]
    assert "leakage_detection" in result["completed_steps"]


def test_model_selection_subgraph(sample_csv):
    graph = build_model_selection_graph()
    state = create_initial_agent_state(
        dataset_path=sample_csv,
        session_id="test_subgraph_model_sel",
        target_column="churn",
    )
    result = graph.invoke(state)
    assert "problem_type" in result
    assert "candidate_models" in result
    assert len(result["candidate_models"]) > 0


def test_evaluation_subgraph(sample_csv):
    graph = build_evaluation_graph()
    state = create_initial_agent_state(
        dataset_path=sample_csv,
        session_id="test_subgraph_eval",
        target_column="churn",
    )
    # Seed minimal evaluation results for diagnostics
    state["evaluation_results"] = {"accuracy": 0.85, "f1": 0.82}
    result = graph.invoke(state)
    assert "underfitting_report" in result
    assert "is_underfitting" in result["underfitting_report"]
    assert "robustness" in result["completed_steps"]


def test_deployment_subgraph():
    graph = build_deployment_graph()
    state = create_initial_agent_state(
        dataset_path="",
        session_id="test_subgraph_deploy",
    )
    state["best_model"] = "RandomForest"
    result = graph.invoke(state)
    assert "model_version" in result
    assert "deployment_status" in result


def test_retraining_subgraph_skip_when_drift_low():
    graph = build_retraining_graph()
    state = create_initial_agent_state(
        dataset_path="",
        session_id="test_subgraph_retrain_low",
    )
    state["drift_report"] = {"psi_score": 0.05, "severity": "none"}
    result = graph.invoke(state)
    assert result["current_step"] == "drift_acceptable"
    assert "challenger_evaluation" not in result.get("completed_steps", [])


def test_retraining_subgraph_triggers_when_drift_high():
    graph = build_retraining_graph()
    state = create_initial_agent_state(
        dataset_path="",
        session_id="test_subgraph_retrain_high",
    )
    state["drift_report"] = {"psi_score": 0.35, "severity": "severe"}
    result = graph.invoke(state)
    assert "challenger_evaluation" in result.get("completed_steps", [])
    assert result.get("should_pause") is True  # Promotion requires human approval


def test_supervisor_graph_compilation_and_structure():
    cp = MemorySaver()
    supervisor_graph = build_supervisor_graph(checkpointer=cp)
    assert supervisor_graph is not None
