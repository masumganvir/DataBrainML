"""
DataWise AI — Central Strongly Typed LangGraph State (Section 5)
Maintains compact metadata, analytical summaries, plans, and artifact paths.
NEVER stores raw datasets inside memory state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """Global Typed State adhering strictly to Master Specification Section 5."""

    # 1. Project & Identification
    project_id: str
    run_id: str
    session_id: str
    dataset_id: str

    # 2. File and Artifact References
    dataset_path: str
    dataset_path_original: str
    dataset_path_analysis: str
    dataset_path_preprocessed: str
    dataset_metadata: Dict[str, Any]
    dataset_profile: Dict[str, Any]

    # 3. Column Classifications
    target_column: Optional[str]
    feature_columns: List[str]
    numerical_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    text_columns: List[str]
    identifier_columns: List[str]

    # 4. Data Quality, Outliers & Missing Values
    data_quality_report: Dict[str, Any]
    missing_value_report: List[Dict[str, Any]]
    outlier_report: List[Dict[str, Any]]

    # 5. Preprocessing & Feature Engineering Plans
    encoding_plan: List[Dict[str, Any]]
    scaling_plan: List[Dict[str, Any]]
    transformation_plan: List[Dict[str, Any]]
    feature_engineering_plan: List[Dict[str, Any]]
    feature_selection_result: List[Dict[str, Any]]
    leakage_report: Dict[str, Any]

    # 6. Visualizations
    visualization_results: List[Dict[str, Any]]

    # 7. Problem & Candidates
    problem_type: str
    candidate_models: List[Dict[str, Any]]

    # 8. Training & Tuning
    training_results: List[Dict[str, Any]]
    cross_validation_results: Dict[str, Any]
    hyperparameter_results: Dict[str, Any]

    # 9. Diagnostics & Explainability
    evaluation_results: Dict[str, Any]
    overfitting_report: Dict[str, Any]
    underfitting_report: Dict[str, Any]
    explainability_report: Dict[str, Any]
    robustness_report: Dict[str, Any]

    # 10. Champion Model & Artifacts
    best_model: str
    model_version: str
    notebook_path: Optional[str]
    report_path: Optional[str]
    model_path: Optional[str]

    # 11. Production & Monitoring
    deployment_status: str
    monitoring_status: str
    drift_report: Dict[str, Any]
    retraining_status: Dict[str, Any]

    # 12. Optimization & Governance
    leaderboard: List[Dict[str, Any]]
    optimization_history: List[Dict[str, Any]]
    production_readiness: Dict[str, Any]
    user_decisions: List[Dict[str, Any]]
    pending_decision: Optional[Dict[str, Any]]
    should_pause: bool
    warnings: List[str]
    errors: List[Dict[str, Any]]
    # 13. Deep Learning & Runtime Flags
    dataset_rows: int

    deep_learning_allowed: bool
    deep_learning_metrics: Dict[str, Any]
    current_agent: str
    current_step: str
    completed_steps: List[str]
    loop_counters: Dict[str, int]



def create_initial_agent_state(
    dataset_path: str,
    session_id: str,
    project_id: Optional[str] = None,
    target_column: Optional[str] = None,
    problem_type: str = "classification",
) -> AgentState:
    """Instantiates a fresh typed state with clean defaults."""
    return {
        "project_id": project_id or session_id,
        "run_id": f"run_{session_id[:8]}",
        "session_id": session_id,
        "dataset_id": f"ds_{session_id[:8]}",
        "dataset_path": dataset_path,
        "dataset_path_original": dataset_path,
        "dataset_metadata": {},
        "dataset_profile": {},
        "target_column": target_column,
        "feature_columns": [],
        "numerical_columns": [],
        "categorical_columns": [],
        "datetime_columns": [],
        "text_columns": [],
        "identifier_columns": [],
        "data_quality_report": {},
        "missing_value_report": [],
        "outlier_report": [],
        "encoding_plan": [],
        "scaling_plan": [],
        "transformation_plan": [],
        "feature_engineering_plan": [],
        "feature_selection_result": [],
        "leakage_report": {},
        "visualization_results": [],
        "problem_type": problem_type,
        "candidate_models": [],
        "training_results": [],
        "cross_validation_results": {},
        "hyperparameter_results": {},
        "evaluation_results": {},
        "overfitting_report": {},
        "underfitting_report": {},
        "explainability_report": {},
        "robustness_report": {},
        "best_model": "",
        "model_version": "v1.0.0",
        "deployment_status": "pending",
        "monitoring_status": "inactive",
        "drift_report": {},
        "retraining_status": {},
        "leaderboard": [],
        "optimization_history": [],
        "production_readiness": {},
        "user_decisions": [],
        "pending_decision": None,
        "should_pause": False,
        "warnings": [],
        "errors": [],
        "current_agent": "supervisor",
        "current_step": "intake",
        "completed_steps": [],
        "loop_counters": {},
    }
