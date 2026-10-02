"""
DataWise AI — Global Data Science State (Section 33)

State contains references to datasets and models on disk, compact summaries,
and plans — never giant raw DataFrames.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, TypedDict
import importlib

# Re-export definitions from app.state.data_science_state if available
try:
    from app.state.data_science_state import (
        ColumnInfo,
        MissingValueReport,
        OutlierReport,
        DecisionRecord,
        DataScienceState as BaseDataScienceState,
        create_initial_state as base_create_initial_state,
    )
except ImportError:
    class ColumnInfo(TypedDict, total=False):
        name: str
        dtype: str
        unique_count: int
        unique_ratio: float
        missing_count: int
        missing_pct: float

    class MissingValueReport(TypedDict, total=False):
        column: str
        missing_count: int
        missing_pct: float
        recommended_strategy: str

    class OutlierReport(TypedDict, total=False):
        column: str
        method: str
        outlier_count: int

    class DecisionRecord(TypedDict, total=False):
        stage: str
        action: str
        approved: bool

    BaseDataScienceState = dict
    base_create_initial_state = None


class DataScienceState(TypedDict, total=False):
    """Global workflow state adhering strictly to Master Specification Section 33."""
    session_id: str
    dataset_id: Optional[str]
    dataset_path: Optional[str]
    dataset_path_original: Optional[str]
    dataset_path_analysis: Optional[str]
    dataset_metadata: Dict[str, Any]
    
    # Analysis reports
    profile: Dict[str, Any]
    quality_report: Dict[str, Any]
    eda_report: Dict[str, Any]
    outlier_report: Dict[str, Any]
    missing_report: Dict[str, Any]
    
    # Plans & Preprocessing
    preprocessing_plan: Dict[str, Any]
    feature_engineering_plan: Dict[str, Any]
    feature_selection_results: Dict[str, Any]
    leakage_report: Dict[str, Any]
    ml_strategy: Dict[str, Any]
    
    # ML & Evaluation
    target_column: Optional[str]
    ml_task_type: Optional[str]
    primary_metric: Optional[str]
    training_results: List[Dict[str, Any]]
    trained_models: List[Dict[str, Any]]
    tuning_results: Dict[str, Any]
    evaluation_results: Dict[str, Any]
    selected_final_model: Optional[str]
    
    # Deliverables & Paths
    final_model_path: Optional[str]
    final_pipeline_path: Optional[str]
    model_metadata_path: Optional[str]
    notebook_path: Optional[str]
    report_path: Optional[str]
    project_bundle_path: Optional[str]
    
    # Workflow & Governance
    user_decisions: List[Dict[str, Any]]
    current_stage: str
    completed_stages: List[str]
    stage_history: List[str]
    checkpoints: Dict[str, str]
    errors: List[str]
    loop_counters: Dict[str, int]
    execution_mode: Literal["guided", "autonomous"]
    status: Literal["idle", "running", "paused_for_approval", "completed", "failed"]


def create_initial_state(
    session_id: str,
    dataset_path: Optional[str] = None,
    dataset_id: Optional[str] = None,
    execution_mode: Literal["guided", "autonomous"] = "guided",
) -> DataScienceState:
    """Factory creating a new DataScienceState instance."""
    if base_create_initial_state is not None and dataset_path:
        base = base_create_initial_state(
            session_id=session_id,
            dataset_path_original=dataset_path,
            dataset_path_analysis=dataset_path,
            execution_mode=execution_mode,
        )
        base["dataset_path"] = dataset_path
        base["dataset_id"] = dataset_id or session_id
        base["loop_counters"] = {
            "outlier_iterations": 0,
            "feature_selection_iterations": 0,
            "tuning_trials": 0,
            "preprocessing_retries": 0,
        }
        return base  # type: ignore

    return {
        "session_id": session_id,
        "dataset_id": dataset_id or session_id,
        "dataset_path": dataset_path,
        "dataset_path_original": dataset_path,
        "dataset_path_analysis": dataset_path,
        "dataset_metadata": {},
        "profile": {},
        "quality_report": {},
        "eda_report": {},
        "outlier_report": {},
        "missing_report": {},
        "preprocessing_plan": {},
        "feature_engineering_plan": {},
        "feature_selection_results": {},
        "leakage_report": {},
        "ml_strategy": {},
        "target_column": None,
        "ml_task_type": None,
        "primary_metric": None,
        "training_results": [],
        "trained_models": [],
        "tuning_results": {},
        "evaluation_results": {},
        "selected_final_model": None,
        "final_model_path": None,
        "final_pipeline_path": None,
        "model_metadata_path": None,
        "notebook_path": None,
        "report_path": None,
        "project_bundle_path": None,
        "user_decisions": [],
        "current_stage": "INITIALIZED",
        "completed_stages": [],
        "stage_history": [],
        "checkpoints": {},
        "errors": [],
        "loop_counters": {
            "outlier_iterations": 0,
            "feature_selection_iterations": 0,
            "tuning_trials": 0,
            "preprocessing_retries": 0,
        },
        "execution_mode": execution_mode,
        "status": "idle",
    }
