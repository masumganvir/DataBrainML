"""
DataWise AI — EDAState Typed Definition
Section 4 Specification: Central LangGraph State for EDA & Visualization Subsystem.
Separates LLM Decision Making from Python Computational Execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class EDAState(TypedDict, total=False):
    """Strongly typed LangGraph state for EDA, Visualization, and Dimensionality Reduction."""

    # 1. Project & Dataset Identifiers
    dataset_id: str
    run_id: str
    project_id: str
    dataset_path: str

    # 2. Schema & Structure
    schema: Dict[str, Any]
    column_types: Dict[str, str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    text_columns: List[str]
    target_column: Optional[str]
    task_type: str
    row_count: int
    column_count: int

    # 3. Profiling & Quality
    dataset_profile: Dict[str, Any]
    data_quality_report: Dict[str, Any]
    missing_summary: Dict[str, Any]
    outlier_summary: Dict[str, Any]
    distribution_summary: Dict[str, Any]
    correlation_summary: Dict[str, Any]
    multicollinearity_report: Dict[str, Any]
    categorical_summary: Dict[str, Any]
    numerical_summary: Dict[str, Any]
    temporal_summary: Dict[str, Any]
    target_summary: Dict[str, Any]
    feature_relationships: Dict[str, Any]

    # 4. Dimensionality Reduction & PCA
    pca_results: Dict[str, Any]
    dimensionality_results: Dict[str, Any]

    # 5. Feature Engineering / Extraction / Selection
    feature_extraction_results: Dict[str, Any]
    feature_selection_results: Dict[str, Any]

    # 6. Visualizations
    visualization_plan: List[Dict[str, Any]]
    visualization_results: List[Dict[str, Any]]
    failed_visualizations: List[Dict[str, Any]]

    # 7. Insights, Summaries & Recommendations
    insights: List[Dict[str, Any]]
    eda_results: Dict[str, Any]
    warnings: List[str]
    errors: List[Dict[str, Any]]
    recommendations: List[str]

    # 8. File Artifacts on Disk
    artifacts: Dict[str, str]

    # 9. Control Flags
    output_dir: str
    current_step: str
    completed_steps: List[str]


def create_initial_eda_state(
    dataset_path: str,
    project_id: str = "proj_default",
    run_id: str = "run_001",
    dataset_id: str = "ds_001",
    target_column: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> EDAState:
    """Creates a clean initial EDAState with defaults."""
    return {
        "dataset_id": dataset_id,
        "run_id": run_id,
        "project_id": project_id,
        "dataset_path": dataset_path,
        "schema": {},
        "column_types": {},
        "numeric_columns": [],
        "categorical_columns": [],
        "datetime_columns": [],
        "text_columns": [],
        "target_column": target_column,
        "task_type": "Auto",
        "row_count": 0,
        "column_count": 0,
        "dataset_profile": {},
        "data_quality_report": {},
        "missing_summary": {},
        "outlier_summary": {},
        "distribution_summary": {},
        "correlation_summary": {},
        "multicollinearity_report": {},
        "categorical_summary": {},
        "numerical_summary": {},
        "temporal_summary": {},
        "target_summary": {},
        "feature_relationships": {},
        "pca_results": {},
        "dimensionality_results": {},
        "feature_extraction_results": {},
        "feature_selection_results": {},
        "visualization_plan": [],
        "visualization_results": [],
        "failed_visualizations": [],
        "insights": [],
        "eda_results": {},
        "warnings": [],
        "errors": [],
        "recommendations": [],
        "artifacts": {},
        "output_dir": output_dir or f"artifacts/{run_id}/visualizations",
        "current_step": "init",
        "completed_steps": [],
    }
