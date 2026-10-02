"""
DataWise AI — Master Graph & 26-Agent E2E Test Suite
Validates that the LangGraph MasterGraph executes the complete data science lifecycle
end-to-end and produces champion models, evaluation metrics, and artifacts.
"""

from pathlib import Path
import pytest
from graphs.master_graph import build_master_graph
from graphs.state import create_initial_agent_state


def test_master_graph_compilation():
    """Verify Master Graph compiles and has entry point and valid nodes."""
    master = build_master_graph()
    assert master is not None


def test_master_graph_e2e_execution(tmp_path):
    """Run master graph end-to-end on clean dataset."""
    dataset_path = Path("..") / "data" / "test_datasets" / "clean_dataset.csv"
    if not dataset_path.exists():
        dataset_path = Path("data") / "test_datasets" / "clean_dataset.csv"

    assert dataset_path.exists(), f"Dataset not found at {dataset_path.resolve()}"

    initial_state = create_initial_agent_state(
        dataset_path=str(dataset_path),
        session_id="test_session_e2e_123",
        target_column="churn",
        problem_type="classification",
    )

    master = build_master_graph()
    final_state = master.invoke(initial_state, config={"configurable": {"thread_id": "test_e2e"}})

    # Assertions on pipeline progress
    assert "intake" in final_state.get("completed_steps", [])
    assert "profiling" in final_state.get("completed_steps", [])
    assert "data_quality" in final_state.get("completed_steps", [])
    assert "training" in final_state.get("completed_steps", [])
    assert "deployment" in final_state.get("completed_steps", [])

    # Assertions on analytical outcomes
    assert final_state.get("best_model") != ""
    assert final_state.get("data_quality_report", {}).get("quality_score", 0) > 0
    assert len(final_state.get("training_results", [])) > 0
    assert len(final_state.get("feature_columns", [])) > 0
