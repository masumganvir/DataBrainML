"""
DataWise AI — LangGraph Shared State

DataScienceState is a TypedDict that flows through all LangGraph nodes.
It stores REFERENCES to datasets and analytical results — NOT raw DataFrames.
Large data is stored on disk; only paths and summaries live in state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


# ------------------------------------------------------------------ #
#  Sub-types
# ------------------------------------------------------------------ #

class ColumnInfo(TypedDict, total=False):
    name: str
    dtype: str
    unique_count: int
    unique_ratio: float
    missing_count: int
    missing_pct: float
    mean: Optional[float]
    median: Optional[float]
    mode: Optional[Any]
    std: Optional[float]
    variance: Optional[float]
    min: Optional[float]
    max: Optional[float]
    q1: Optional[float]
    q3: Optional[float]
    iqr: Optional[float]
    skewness: Optional[float]
    kurtosis: Optional[float]
    zero_count: Optional[int]
    negative_count: Optional[int]
    is_identifier: bool
    is_constant: bool
    is_near_constant: bool


class MissingValueReport(TypedDict, total=False):
    column: str
    missing_count: int
    missing_pct: float
    dtype: str
    severity: Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommended_strategy: str
    alternative_strategies: List[str]
    explanation: str


class OutlierReport(TypedDict, total=False):
    column: str
    method: str
    outlier_count: int
    outlier_pct: float
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    severity: Literal["none", "mild", "moderate", "severe"]
    interpretation: str


class VisualizationResult(TypedDict, total=False):
    artifact_id: str
    column: Optional[str]
    chart_type: str
    file_path: str
    file_format: str
    title: str
    ai_interpretation: str


class PreprocessingDecision(TypedDict, total=False):
    column: str
    operation: str          # impute | encode | scale | transform | drop | keep
    method: str             # e.g. median | StandardScaler | OneHotEncoder
    approved: bool
    user_override: Optional[str]


class FeatureSelectionResult(TypedDict, total=False):
    column: str
    method: str
    score: float
    selected: bool
    reason: str


class ModelRecommendation(TypedDict, total=False):
    model_name: str
    model_class: str
    rationale: str
    pros: List[str]
    cons: List[str]
    evaluation_metrics: List[str]


class PipelineDefinition(TypedDict, total=False):
    numerical_columns: List[str]
    categorical_columns: List[str]
    numerical_imputer: str
    numerical_scaler: Optional[str]
    numerical_transformer: Optional[str]
    categorical_imputer: str
    categorical_encoder: str
    selected_features: List[str]
    target_column: str
    task_type: str
    generated_code: str


class OutlierDecisionItem(TypedDict, total=False):
    column: str
    row_indices: List[int]
    outlier_count: int
    outlier_pct: float
    detection_methods: List[str]
    distance_from_range: float
    target_association: Optional[str]
    class_association: Optional[Dict[str, float]]
    classified_as: Literal["data_entry_error", "measurement_error", "legitimate_rare", "target_signal", "unknown"]
    recommended_action: Literal["KEEP", "REMOVE", "CAP", "WINSORIZE", "TRANSFORM", "INVESTIGATE"]
    rationale: str
    confidence: Literal["HIGH", "MEDIUM", "LOW", "NEEDS_HUMAN_REVIEW"]


class TrainedModelResult(TypedDict, total=False):
    model_name: str
    model_class: str
    cv_scores: List[float]
    cv_mean: float
    cv_std: float
    test_metrics: Dict[str, float]
    training_time_seconds: float
    hyperparameters: Dict[str, Any]
    is_selected: bool
    selection_rationale: Optional[str]


class ModelExplainabilityResult(TypedDict, total=False):
    model_name: str
    feature_importances: Dict[str, float]
    permutation_importances: Dict[str, float]
    coefficients: Optional[Dict[str, float]]
    top_predictive_features: List[str]
    model_limitations: List[str]


class ProductionReadinessReport(TypedDict, total=False):
    status: Literal["PASS", "WARNING", "FAIL"]
    score: float
    checklist: List[Dict[str, Any]]
    reasons: List[str]


# ------------------------------------------------------------------ #
#  Main State
# ------------------------------------------------------------------ #

class DataScienceState(TypedDict, total=False):
    """
    Central LangGraph state shared across all agent nodes.
    Convention: never store raw DataFrames — store file paths and summaries.
    """

    # --- Session / Identification ---
    session_id: str
    dataset_id: str

    # --- Dataset Paths (versioned, never overwrite original) ---
    dataset_path_original: str       # path to the untouched uploaded file
    dataset_path_analysis: str       # copy used for read-only analysis
    dataset_path_preprocessed: str   # after approved transformations
    dataset_path_feature_eng: str    # after feature engineering
    dataset_path_final: str          # final ML-ready dataset

    # --- Schema ---
    dataset_metadata: Dict[str, Any]  # filename, format, size, row_count, col_count
    dataframe_schema: Dict[str, str]  # {col_name: dtype_str}
    sample_rows: List[Dict[str, Any]] # first 5 rows for display

    # --- Column Classification ---
    numerical_columns: List[str]
    categorical_columns: List[str]
    binary_columns: List[str]
    datetime_columns: List[str]
    text_columns: List[str]
    identifier_columns: List[str]
    constant_columns: List[str]
    near_constant_columns: List[str]

    # --- Target ---
    target_column: Optional[str]
    target_candidates: List[str]
    task_type: Optional[Literal["classification", "regression", "clustering", "time_series"]]
    class_distribution: Optional[Dict[str, int]]
    imbalance_ratio: Optional[float]

    # --- Analysis Reports (dicts/lists, NOT DataFrames) ---
    column_profiles: List[ColumnInfo]
    missing_value_report: List[MissingValueReport]
    duplicate_report: Dict[str, Any]   # {count, pct, examples}
    outlier_report: List[OutlierReport]
    distribution_report: Dict[str, Any]
    correlation_report: Dict[str, Any]  # {pearson_matrix_path, spearman_matrix_path, highly_correlated_pairs}

    # --- Visualization ---
    visualization_plan: List[str]       # planned chart types
    visualization_results: List[VisualizationResult]

    # --- Preprocessing Plans ---
    preprocessing_plan: List[PreprocessingDecision]
    encoding_plan: List[Dict[str, Any]]
    scaling_plan: List[Dict[str, Any]]
    transformation_plan: List[Dict[str, Any]]

    # --- Feature Engineering ---
    feature_engineering_plan: List[Dict[str, Any]]
    engineered_features: List[str]

    # --- Feature Selection ---
    feature_selection_results: List[FeatureSelectionResult]
    selected_features: List[str]

    # --- Leakage ---
    leakage_warnings: List[Dict[str, Any]]

    # --- ML Readiness ---
    ml_readiness_score: Optional[float]
    ml_readiness_level: Optional[Literal["NOT_READY", "NEEDS_PREPROCESSING", "READY_FOR_BASELINE"]]
    ml_readiness_report: Dict[str, Any]

    # --- Pipeline ---
    pipeline_definition: PipelineDefinition
    generated_pipeline_code: str

    # --- ML Recommendations ---
    model_recommendations: List[ModelRecommendation]
    evaluation_plan: Dict[str, Any]

    # --- Human-in-the-Loop ---
    pending_decision: Optional[Dict[str, Any]]   # question currently awaiting user input
    user_decisions: List[Dict[str, Any]]          # all decisions made so far

    # --- Conversation ---
    conversation_history: List[Dict[str, str]]    # [{role, content}]
    last_user_message: str

    # --- Generated Artifacts ---
    generated_artifacts: List[str]    # artifact IDs

    # --- Workflow Control ---
    current_stage: str                # current workflow stage name
    completed_stages: List[str]       # stages finished
    errors: List[Dict[str, Any]]      # {stage, error, timestamp}
    should_continue: bool             # False → human input required
    next_stage: Optional[str]         # explicit override for next node

    # --- LLM Usage Tracking ---
    total_llm_calls: int
    total_tokens_used: int

    # --- Domain & Objective Context ---
    dataset_domain: Optional[str]
    prediction_objective: Optional[str]
    execution_mode: Optional[Literal["guided", "autonomous"]]

    # --- Advanced Outlier Decisions ---
    outlier_decisions: List[OutlierDecisionItem]

    # --- Model Training & Evaluation ---
    trained_models: List[TrainedModelResult]
    selected_final_model: Optional[str]
    primary_metric: Optional[str]
    cv_strategy: Optional[str]

    # --- Explainability & Limitations ---
    model_explainability: Optional[ModelExplainabilityResult]
    dataset_shift_report: Optional[Dict[str, Any]]
    production_readiness: Optional[ProductionReadinessReport]

    # --- Production Artifacts ---
    final_pipeline_path: Optional[str]
    model_metadata_path: Optional[str]
    notebook_path: Optional[str]
    project_bundle_path: Optional[str]
    decision_log: List[Dict[str, Any]]
