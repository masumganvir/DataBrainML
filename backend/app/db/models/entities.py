"""DataWise AI — Production Enterprise Database Schema (SQLAlchemy 2.x)

Features 37 core entities spanning:
  - Users, Auth, Sessions, API Keys, RBAC
  - Projects, Multi-tenancy
  - Datasets, Versions, Columns, Profiles, Quality Reports
  - Experiments, Runs, Preprocessing Runs, Features
  - Model Candidates, Training Runs, Metrics, Cross-Validation, Hyperparameter Runs
  - Evaluation, Overfitting, Explainability, Robustness
  - Model Registry (Models, Immutable Model Versions)
  - Artifact Management (Metadata in DB, Binaries in Object Storage)
  - Notebooks, Reports
  - Deployments, Prediction Requests, Monitoring & Drift Detection
  - Agent Observability (Agent Runs, Agent Events)
  - User Decisions (Human-in-the-Loop traceability)
  - Audit Logs (Append-Only)
  - Background Jobs (Redis-backed worker tracking)
  - Usage & Cost Tracking (Billing-ready)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    __allow_unmapped__ = True


def _uuid() -> str:
    return str(uuid.uuid4())


# ================================================================== #
#  1. USERS, AUTH & ACCESS CONTROL
# ================================================================== #

class User(Base):
    """Primary user identity with authentication and status."""
    __tablename__ = "users"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    role: str = Column(String(50), default="data_scientist", nullable=False)  # owner | admin | developer | data_scientist | viewer
    status: str = Column(String(50), default="active", nullable=False, index=True)  # active | suspended | pending
    is_active: bool = Column(Boolean, default=True, nullable=False)
    organization_id: Optional[str] = Column(String(36), nullable=True, index=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at: Optional[datetime] = Column(DateTime, nullable=True)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    sessions: list[UserSession] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys: list[ApiKey] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    projects: list[Project] = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    audit_logs: list[AuditLog] = relationship("AuditLog", back_populates="user")


class UserSession(Base):
    """User authentication session tokens."""
    __tablename__ = "user_sessions"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    user_id: str = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: str = Column(String(255), nullable=False, index=True)
    expires_at: datetime = Column(DateTime, nullable=False, index=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    revoked_at: Optional[datetime] = Column(DateTime, nullable=True)

    user: User = relationship("User", back_populates="sessions")


class ApiKey(Base):
    """Hashed API keys for programmatic access with scoped permissions."""
    __tablename__ = "api_keys"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    user_id: str = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    key_hash: str = Column(String(255), nullable=False)
    key_prefix: str = Column(String(16), nullable=False, index=True)
    permissions: dict = Column(JSON, default=list, nullable=False)
    last_used_at: Optional[datetime] = Column(DateTime, nullable=True)
    expires_at: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    revoked_at: Optional[datetime] = Column(DateTime, nullable=True)

    user: User = relationship("User", back_populates="api_keys")


# ================================================================== #
#  2. PROJECTS & WORKSPACES
# ================================================================== #

class Project(Base):
    """Top-level workspace grouping datasets, experiments, models, and deployments."""
    __tablename__ = "projects"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    user_id: str = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Optional[str] = Column(String(36), nullable=True, index=True)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    status: str = Column(String(50), default="active", nullable=False, index=True)
    configuration: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    owner: User = relationship("User", back_populates="projects")
    datasets: list[DatasetEntity] = relationship("DatasetEntity", back_populates="project", cascade="all, delete-orphan")
    experiments: list[Experiment] = relationship("Experiment", back_populates="project", cascade="all, delete-orphan")
    models: list[ModelEntity] = relationship("ModelEntity", back_populates="project", cascade="all, delete-orphan")
    artifacts: list[ArtifactEntity] = relationship("ArtifactEntity", back_populates="project", cascade="all, delete-orphan")
    notebooks: list[Notebook] = relationship("Notebook", back_populates="project", cascade="all, delete-orphan")
    reports: list[Report] = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    jobs: list[BackgroundJob] = relationship("BackgroundJob", back_populates="project", cascade="all, delete-orphan")


# ================================================================== #
#  3. DATASETS & DATASET LINEAGE
# ================================================================== #

class DatasetEntity(Base):
    """Dataset metadata repository pointing to object storage."""
    __tablename__ = "datasets"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: Optional[str] = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    # Backward compatibility with existing sessions
    session_id: Optional[str] = Column(String(36), nullable=True, index=True)
    name: Optional[str] = Column(String(255), nullable=True, default="")
    original_filename: str = Column(String(255), nullable=False)
    file_type: str = Column(String(50), default="csv", nullable=False)
    mime_type: Optional[str] = Column(String(100), default="text/csv", nullable=True)
    file_size: int = Column(BigInteger, default=0, nullable=False)
    storage_key: Optional[str] = Column(String(1024), nullable=True)
    storage_bucket: Optional[str] = Column(String(255), nullable=True)
    checksum: Optional[str] = Column(String(64), nullable=True, index=True)
    row_count: Optional[int] = Column(Integer, nullable=True)
    column_count: Optional[int] = Column(Integer, nullable=True)
    status: str = Column(String(50), default="ready", nullable=False, index=True)
    version: str = Column(String(50), default="1.0.0", nullable=False)
    entity_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    # Legacy fields for existing endpoints
    stored_filename: Optional[str] = Column(String(255), nullable=True)
    file_path: Optional[str] = Column(String(1024), nullable=True)
    file_format: Optional[str] = Column(String(20), nullable=True)
    file_size_bytes: Optional[int] = Column(Integer, nullable=True)
    schema_info: Optional[dict] = Column(JSON, nullable=True)
    profile_summary: Optional[dict] = Column(JSON, nullable=True)
    quality_summary: Optional[dict] = Column(JSON, nullable=True)

    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    project: Optional[Project] = relationship("Project", back_populates="datasets")
    versions: list[DatasetVersion] = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base):
    """Immutable version snapshot of a dataset."""
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version", name="uq_dataset_version"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    dataset_id: str = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version: str = Column(String(50), nullable=False)
    storage_key: str = Column(String(1024), nullable=False)
    checksum: str = Column(String(64), nullable=False)
    row_count: int = Column(Integer, default=0, nullable=False)
    column_count: int = Column(Integer, default=0, nullable=False)
    schema_definition: Optional[dict] = Column("schema", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    dataset: DatasetEntity = relationship("DatasetEntity", back_populates="versions")
    columns: list[DatasetColumn] = relationship("DatasetColumn", back_populates="dataset_version", cascade="all, delete-orphan")
    profiles: list[DatasetProfile] = relationship("DatasetProfile", back_populates="dataset_version", cascade="all, delete-orphan")
    quality_reports: list[DataQualityReport] = relationship("DataQualityReport", back_populates="dataset_version", cascade="all, delete-orphan")
    experiments: list[Experiment] = relationship("Experiment", back_populates="dataset_version")


class DatasetColumn(Base):
    """Detailed profile and statistics per dataset column."""
    __tablename__ = "dataset_columns"
    __table_args__ = (
        Index("ix_dataset_columns_version_name", "dataset_version_id", "column_name"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: str = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name: str = Column(String(255), nullable=False)
    data_type: str = Column(String(100), nullable=False)
    semantic_type: Optional[str] = Column(String(100), nullable=True)
    nullable: bool = Column(Boolean, default=True, nullable=False)
    unique_count: int = Column(Integer, default=0, nullable=False)
    missing_count: int = Column(Integer, default=0, nullable=False)
    missing_percentage: float = Column(Float, default=0.0, nullable=False)
    statistics: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    dataset_version: DatasetVersion = relationship("DatasetVersion", back_populates="columns")


class DatasetProfile(Base):
    """Comprehensive profiling report generated by profiling agents."""
    __tablename__ = "dataset_profiles"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: str = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    profile: dict = Column(JSON, nullable=False)
    quality_score: Optional[float] = Column(Float, nullable=True)
    generated_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    agent_run_id: Optional[str] = Column(String(36), nullable=True)

    dataset_version: DatasetVersion = relationship("DatasetVersion", back_populates="profiles")


class DataQualityReport(Base):
    """Data quality analysis report and identified anomalies."""
    __tablename__ = "data_quality_reports"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: str = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    report: dict = Column(JSON, nullable=False)
    severity: str = Column(String(50), default="low", nullable=False)  # low | medium | high | critical
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    agent_run_id: Optional[str] = Column(String(36), nullable=True)

    dataset_version: DatasetVersion = relationship("DatasetVersion", back_populates="quality_reports")


# ================================================================== #
#  4. EXPERIMENTS & RUNS
# ================================================================== #

class Experiment(Base):
    """Machine learning experiment container."""
    __tablename__ = "experiments"
    __table_args__ = (
        Index("ix_experiments_project_status", "project_id", "status"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id: Optional[str] = Column(String(36), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    name: str = Column(String(255), nullable=False)
    problem_type: str = Column(String(100), nullable=False)  # classification | regression | clustering | time_series
    target_column: Optional[str] = Column(String(255), nullable=True)
    objective_metric: str = Column(String(100), default="accuracy", nullable=False)
    status: str = Column(String(50), default="created", nullable=False, index=True)  # created | queued | running | waiting_for_user | completed | failed | cancelled
    configuration: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)

    project: Project = relationship("Project", back_populates="experiments")
    dataset_version: Optional[DatasetVersion] = relationship("DatasetVersion", back_populates="experiments")
    runs: list[ExperimentRun] = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    features: list[Feature] = relationship("Feature", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentRun(Base):
    """A specific execution iteration of an experiment."""
    __tablename__ = "experiment_runs"
    __table_args__ = (
        Index("ix_experiment_runs_exp_status", "experiment_id", "status"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_id: str = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number: int = Column(Integer, default=1, nullable=False)
    status: str = Column(String(50), default="running", nullable=False, index=True)
    started_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    configuration: Optional[dict] = Column(JSON, nullable=True)
    error: Optional[dict] = Column(JSON, nullable=True)

    experiment: Experiment = relationship("Experiment", back_populates="runs")
    preprocessing_runs: list[PreprocessingRun] = relationship("PreprocessingRun", back_populates="experiment_run", cascade="all, delete-orphan")
    model_candidates: list[ModelCandidate] = relationship("ModelCandidate", back_populates="experiment_run", cascade="all, delete-orphan")
    training_runs: list[TrainingRun] = relationship("TrainingRun", back_populates="experiment_run", cascade="all, delete-orphan")


class PreprocessingRun(Base):
    """Preprocessing and feature transformation record."""
    __tablename__ = "preprocessing_runs"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_run_id: str = Column(String(36), ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy: Optional[dict] = Column(JSON, nullable=True)
    input_schema: Optional[dict] = Column(JSON, nullable=True)
    output_schema: Optional[dict] = Column(JSON, nullable=True)
    transformations: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    experiment_run: ExperimentRun = relationship("ExperimentRun", back_populates="preprocessing_runs")


class Feature(Base):
    """Engineered and selected features for an experiment."""
    __tablename__ = "features"
    __table_args__ = (
        Index("ix_features_exp_selected", "experiment_id", "selected"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_id: str = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    source_column: Optional[str] = Column(String(255), nullable=True)
    feature_type: str = Column(String(100), nullable=False)
    transformation: Optional[str] = Column(String(255), nullable=True)
    importance: Optional[float] = Column(Float, nullable=True)
    selected: bool = Column(Boolean, default=True, nullable=False)
    feature_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    experiment: Experiment = relationship("Experiment", back_populates="features")


# ================================================================== #
#  5. MODEL CANDIDATES & TRAINING RUNS
# ================================================================== #

class ModelCandidate(Base):
    """Algorithm candidate considered for an experiment run."""
    __tablename__ = "model_candidates"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_run_id: str = Column(String(36), ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    algorithm: str = Column(String(100), nullable=False)  # e.g. RandomForest, LightGBM
    library: str = Column(String(100), nullable=False)    # scikit-learn, xgboost
    hyperparameters: Optional[dict] = Column(JSON, nullable=True)
    status: str = Column(String(50), default="candidate", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    experiment_run: ExperimentRun = relationship("ExperimentRun", back_populates="model_candidates")
    training_runs: list[TrainingRun] = relationship("TrainingRun", back_populates="model_candidate")


class TrainingRun(Base):
    """Execution of model training, evaluation, and hyperparameter search."""
    __tablename__ = "training_runs"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_run_id: str = Column(String(36), ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    model_candidate_id: Optional[str] = Column(String(36), ForeignKey("model_candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    status: str = Column(String(50), default="running", nullable=False, index=True)
    started_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    training_time_ms: Optional[int] = Column(Integer, nullable=True)
    configuration: Optional[dict] = Column(JSON, nullable=True)
    error: Optional[dict] = Column(JSON, nullable=True)

    experiment_run: ExperimentRun = relationship("ExperimentRun", back_populates="training_runs")
    model_candidate: Optional[ModelCandidate] = relationship("ModelCandidate", back_populates="training_runs")
    metrics: list[ModelMetric] = relationship("ModelMetric", back_populates="training_run", cascade="all, delete-orphan")
    cross_validation: list[CrossValidationResult] = relationship("CrossValidationResult", back_populates="training_run", cascade="all, delete-orphan")
    hyperparameter_runs: list[HyperparameterRun] = relationship("HyperparameterRun", back_populates="training_run", cascade="all, delete-orphan")
    evaluation_results: list[EvaluationResult] = relationship("EvaluationResult", back_populates="training_run", cascade="all, delete-orphan")
    overfitting_reports: list[OverfittingReport] = relationship("OverfittingReport", back_populates="training_run", cascade="all, delete-orphan")
    explainability_results: list[ExplainabilityResult] = relationship("ExplainabilityResult", back_populates="training_run", cascade="all, delete-orphan")
    robustness_results: list[RobustnessResult] = relationship("RobustnessResult", back_populates="training_run", cascade="all, delete-orphan")


class ModelMetric(Base):
    """Detailed atomic metrics recorded during model training and evaluation."""
    __tablename__ = "model_metrics"
    __table_args__ = (
        Index("ix_model_metrics_lookup", "training_run_id", "metric_name", "dataset_split"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: str = Column(String(100), nullable=False)
    metric_value: float = Column(Float, nullable=False)
    dataset_split: str = Column(String(50), default="test", nullable=False)  # train | validation | test
    fold_number: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="metrics")


class CrossValidationResult(Base):
    """Stratified or k-fold cross-validation aggregated scores."""
    __tablename__ = "cross_validation_results"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy: str = Column(String(100), nullable=False)
    fold_count: int = Column(Integer, default=5, nullable=False)
    mean_score: float = Column(Float, nullable=False)
    std_score: float = Column(Float, default=0.0, nullable=False)
    scores: dict = Column(JSON, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="cross_validation")


class HyperparameterRun(Base):
    """Optuna / bayesian hyperparameter optimization trial logs."""
    __tablename__ = "hyperparameter_runs"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    optimizer: str = Column(String(100), default="optuna", nullable=False)
    search_space: Optional[dict] = Column(JSON, nullable=True)
    best_parameters: Optional[dict] = Column(JSON, nullable=True)
    best_score: Optional[float] = Column(Float, nullable=True)
    trials: int = Column(Integer, default=0, nullable=False)
    budget: Optional[dict] = Column(JSON, nullable=True)
    started_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="hyperparameter_runs")


class EvaluationResult(Base):
    """Full evaluation breakdown: confusion matrix, residuals, classification report."""
    __tablename__ = "evaluation_results"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    metrics: dict = Column(JSON, nullable=False)
    confusion_matrix: Optional[dict] = Column(JSON, nullable=True)
    classification_report: Optional[dict] = Column(JSON, nullable=True)
    residual_statistics: Optional[dict] = Column(JSON, nullable=True)
    evaluation_metadata: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="evaluation_results")


class OverfittingReport(Base):
    """Train vs test divergence, regularization checks, and leakage diagnostics."""
    __tablename__ = "overfitting_reports"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    training_metrics: dict = Column(JSON, nullable=False)
    validation_metrics: dict = Column(JSON, nullable=False)
    test_metrics: dict = Column(JSON, nullable=False)
    status: str = Column(String(50), default="healthy", nullable=False)  # healthy | overfitting | underfitting
    analysis: dict = Column(JSON, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="overfitting_reports")


class ExplainabilityResult(Base):
    """SHAP, feature importances, and local counterfactual explanations."""
    __tablename__ = "explainability_results"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    method: str = Column(String(100), default="tree_shap", nullable=False)
    global_importance: dict = Column(JSON, nullable=False)
    local_explanations: Optional[dict] = Column(JSON, nullable=True)
    artifact_id: Optional[str] = Column(String(36), nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="explainability_results")


class RobustnessResult(Base):
    """Stress testing, noise resilience, and adversarial perturbation results."""
    __tablename__ = "robustness_results"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    training_run_id: str = Column(String(36), ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tests: dict = Column(JSON, nullable=False)
    overall_result: str = Column(String(50), default="passed", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)

    training_run: TrainingRun = relationship("TrainingRun", back_populates="robustness_results")


# ================================================================== #
#  6. MODEL REGISTRY (IMMUTABLE PRODUCTION VERSIONS)
# ================================================================== #

class ModelEntity(Base):
    """Registered ML model catalog."""
    __tablename__ = "models"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    problem_type: str = Column(String(100), nullable=False)
    status: str = Column(String(50), default="development", nullable=False, index=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Project = relationship("Project", back_populates="models")
    versions: list[ModelVersion] = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")


class ModelVersion(Base):
    """Immutable model version snapshot."""
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_id", "version", name="uq_model_version"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    model_id: str = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    version: str = Column(String(50), nullable=False)
    training_run_id: Optional[str] = Column(String(36), ForeignKey("training_runs.id", ondelete="SET NULL"), nullable=True)
    artifact_id: Optional[str] = Column(String(36), nullable=True)
    framework: str = Column(String(100), nullable=False)          # scikit-learn | lightgbm | xgboost | pytorch
    framework_version: Optional[str] = Column(String(50), nullable=True)
    python_version: Optional[str] = Column(String(50), nullable=True)
    model_type: str = Column(String(100), nullable=False)
    input_schema: Optional[dict] = Column(JSON, nullable=True)
    output_schema: Optional[dict] = Column(JSON, nullable=True)
    metrics: Optional[dict] = Column(JSON, nullable=True)
    parameters: Optional[dict] = Column(JSON, nullable=True)
    feature_list: Optional[dict] = Column(JSON, nullable=True)
    dataset_hash: Optional[str] = Column(String(64), nullable=True)
    code_hash: Optional[str] = Column(String(64), nullable=True)
    status: str = Column(String(50), default="development", nullable=False, index=True)  # development | testing | staging | production | archived
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    promoted_at: Optional[datetime] = Column(DateTime, nullable=True)
    archived_at: Optional[datetime] = Column(DateTime, nullable=True)

    model: ModelEntity = relationship("ModelEntity", back_populates="versions")
    deployments: list[Deployment] = relationship("Deployment", back_populates="model_version")


# ================================================================== #
#  7. ARTIFACTS & STORAGE METADATA
# ================================================================== #

class ArtifactEntity(Base):
    """Artifact metadata record. Binary contents stored in S3/MinIO."""
    __tablename__ = "artifacts"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: Optional[str] = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id: Optional[str] = Column(String(36), nullable=True, index=True)
    artifact_type: str = Column(String(50), nullable=False)  # dataset | model | plot | notebook | report | joblib | onnx | json
    filename: Optional[str] = Column(String(255), nullable=True, default="")
    storage_provider: str = Column(String(50), default="s3", nullable=False)  # s3 | minio | local
    bucket: str = Column(String(255), default="datawise-artifacts", nullable=False)
    storage_key: Optional[str] = Column(String(1024), nullable=True, default="")
    content_type: str = Column(String(100), default="application/octet-stream", nullable=False)
    size_bytes: int = Column(BigInteger, default=0, nullable=False)
    checksum: Optional[str] = Column(String(64), nullable=True)
    artifact_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    # Legacy fields
    name: Optional[str] = Column(String(255), nullable=True)
    description: Optional[str] = Column(Text, nullable=True)
    file_path: Optional[str] = Column(String(1024), nullable=True)
    file_format: Optional[str] = Column(String(20), nullable=True)
    file_size_bytes: Optional[int] = Column(Integer, default=0)

    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    project: Optional[Project] = relationship("Project", back_populates="artifacts")


class Notebook(Base):
    """Automated reproducible Jupyter notebooks."""
    __tablename__ = "notebooks"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id: Optional[str] = Column(String(36), nullable=True)
    experiment_run_id: Optional[str] = Column(String(36), nullable=True)
    artifact_id: Optional[str] = Column(String(36), nullable=True)
    status: str = Column(String(50), default="generated", nullable=False)
    jupyter_version: Optional[str] = Column(String(50), default="7.0", nullable=True)
    generated_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    executed_at: Optional[datetime] = Column(DateTime, nullable=True)
    execution_status: Optional[str] = Column(String(50), nullable=True)
    notebook_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)

    project: Project = relationship("Project", back_populates="notebooks")


class Report(Base):
    """Generated executive and technical PDF/HTML reports."""
    __tablename__ = "reports"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    experiment_run_id: Optional[str] = Column(String(36), nullable=True)
    report_type: str = Column(String(50), nullable=False)  # executive | technical | eda | evaluation
    artifact_id: Optional[str] = Column(String(36), nullable=True)
    format: str = Column(String(20), default="PDF", nullable=False)  # PDF | HTML | JSON | Markdown
    status: str = Column(String(50), default="generated", nullable=False)
    generated_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    report_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)

    project: Project = relationship("Project", back_populates="reports")


# ================================================================== #
#  8. DEPLOYMENTS, PREDICTIONS & MONITORING
# ================================================================== #

class Deployment(Base):
    """Model deployment endpoints (dev, staging, prod)."""
    __tablename__ = "deployments"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    model_version_id: str = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    environment: str = Column(String(50), default="development", nullable=False)  # development | staging | production
    endpoint: str = Column(String(255), nullable=False)
    status: str = Column(String(50), default="pending", nullable=False, index=True)  # pending | deploying | healthy | unhealthy | rolled_back | terminated
    deployment_type: str = Column(String(50), default="realtime", nullable=False)   # realtime | batch | serverless
    configuration: Optional[dict] = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deployed_at: Optional[datetime] = Column(DateTime, nullable=True)
    rolled_back_at: Optional[datetime] = Column(DateTime, nullable=True)

    model_version: ModelVersion = relationship("ModelVersion", back_populates="deployments")
    predictions: list[PredictionRequest] = relationship("PredictionRequest", back_populates="deployment", cascade="all, delete-orphan")
    monitoring_metrics: list[MonitoringMetric] = relationship("MonitoringMetric", back_populates="deployment", cascade="all, delete-orphan")
    drift_reports: list[DriftReport] = relationship("DriftReport", back_populates="deployment", cascade="all, delete-orphan")


class PredictionRequest(Base):
    """Inference telemetry and audit records with configurable retention."""
    __tablename__ = "prediction_requests"
    __table_args__ = (
        Index("ix_prediction_requests_dep_created", "deployment_id", "created_at"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    deployment_id: str = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id: str = Column(String(64), nullable=False, index=True)
    input_hash: str = Column(String(64), nullable=False)
    prediction: dict = Column(JSON, nullable=False)
    confidence: Optional[dict] = Column(JSON, nullable=True)
    latency_ms: float = Column(Float, nullable=False)
    status: str = Column(String(50), default="success", nullable=False)
    error: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    deployment: Deployment = relationship("Deployment", back_populates="predictions")


class MonitoringMetric(Base):
    """Aggregated production monitoring metrics over time windows."""
    __tablename__ = "monitoring_metrics"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    deployment_id: str = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name: str = Column(String(100), nullable=False)
    metric_value: float = Column(Float, nullable=False)
    metric_window: str = Column(String(50), default="1h", nullable=False)  # 5m | 1h | 24h
    metric_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    deployment: Deployment = relationship("Deployment", back_populates="monitoring_metrics")


class DriftReport(Base):
    """Covariate and prediction drift analysis reports."""
    __tablename__ = "drift_reports"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    deployment_id: str = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_reference: Optional[str] = Column(String(255), nullable=True)
    feature_drift: dict = Column(JSON, nullable=False)
    prediction_drift: Optional[dict] = Column(JSON, nullable=True)
    performance_drift: Optional[dict] = Column(JSON, nullable=True)
    severity: str = Column(String(50), default="low", nullable=False)  # low | medium | high
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    deployment: Deployment = relationship("Deployment", back_populates="drift_reports")


# ================================================================== #
#  9. AGENT OBSERVABILITY & USER DECISIONS
# ================================================================== #

class AgentRun(Base):
    """Observability record of LangGraph agent executions."""
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_lookup", "project_id", "experiment_run_id", "agent_name", "status"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: Optional[str] = Column(String(36), nullable=True, index=True)
    experiment_run_id: Optional[str] = Column(String(36), nullable=True, index=True)
    agent_name: str = Column(String(100), nullable=False, index=True)
    agent_version: str = Column(String(50), default="1.0.0", nullable=False)
    status: str = Column(String(50), default="running", nullable=False, index=True)
    started_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    duration_ms: Optional[int] = Column(Integer, nullable=True)
    input_reference: Optional[dict] = Column(JSON, nullable=True)
    output_reference: Optional[dict] = Column(JSON, nullable=True)
    error: Optional[dict] = Column(JSON, nullable=True)
    retry_count: int = Column(Integer, default=0, nullable=False)
    agent_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)

    events: list[AgentEvent] = relationship("AgentEvent", back_populates="agent_run", cascade="all, delete-orphan")


class AgentEvent(Base):
    """Granular agent lifecycle and tool invocation events."""
    __tablename__ = "agent_events"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    agent_run_id: str = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: str = Column(String(100), nullable=False)  # start | step | tool_call | tool_result | complete | error
    message: str = Column(Text, nullable=False)
    payload: Optional[dict] = Column(JSON, nullable=True)
    timestamp: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    agent_run: AgentRun = relationship("AgentRun", back_populates="events")


class UserDecisionRecord(Base):
    """Traceability for Human-In-The-Loop approvals and choices."""
    __tablename__ = "user_decisions"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: Optional[str] = Column(String(36), nullable=True, index=True)
    experiment_run_id: Optional[str] = Column(String(36), nullable=True, index=True)
    agent_run_id: Optional[str] = Column(String(36), nullable=True, index=True)
    # Legacy fields
    session_id: Optional[str] = Column(String(36), nullable=True, index=True)
    stage: Optional[str] = Column(String(100), nullable=True)
    decision_key: Optional[str] = Column(String(255), nullable=True)
    decision_value: Optional[str] = Column(Text, nullable=True)
    context: Optional[dict] = Column(JSON, nullable=True)

    decision_type: str = Column(String(100), default="general", nullable=False)
    question: Optional[str] = Column(Text, nullable=True)
    options: Optional[dict] = Column(JSON, nullable=True)
    selected_option: Optional[str] = Column(Text, nullable=True)
    reason: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)


# ================================================================== #
#  10. AUDIT LOGS, BACKGROUND JOBS & BILLING
# ================================================================== #

class AuditLog(Base):
    """Immutable, append-only security and operational audit trail."""
    __tablename__ = "audit_logs"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    user_id: Optional[str] = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id: Optional[str] = Column(String(36), nullable=True, index=True)
    action: str = Column(String(100), nullable=False, index=True)  # login | upload | train | promote | deploy | delete
    resource_type: str = Column(String(100), nullable=False)
    resource_id: Optional[str] = Column(String(36), nullable=True)
    ip_hash: Optional[str] = Column(String(64), nullable=True)
    user_agent: Optional[str] = Column(String(255), nullable=True)
    audit_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    user: Optional[User] = relationship("User", back_populates="audit_logs")


class BackgroundJob(Base):
    """Redis-backed distributed worker job tracking."""
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_type_status_priority", "job_type", "status", "priority"),
    )

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: Optional[str] = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type: str = Column(String(100), nullable=False)  # profiling | training | tuning | report | notebook
    status: str = Column(String(50), default="pending", nullable=False, index=True)  # pending | running | completed | failed | cancelled
    priority: int = Column(Integer, default=10, nullable=False)  # 1 (low) to 10 (high)
    queue: str = Column(String(100), default="default", nullable=False)
    payload: Optional[dict] = Column(JSON, nullable=True)
    result: Optional[dict] = Column(JSON, nullable=True)
    error: Optional[dict] = Column(JSON, nullable=True)
    attempts: int = Column(Integer, default=0, nullable=False)
    max_attempts: int = Column(Integer, default=3, nullable=False)
    scheduled_at: Optional[datetime] = Column(DateTime, nullable=True)
    started_at: Optional[datetime] = Column(DateTime, nullable=True)
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    project: Optional[Project] = relationship("Project", back_populates="jobs")


class UsageRecord(Base):
    """Resource consumption records for cost tracking and billing."""
    __tablename__ = "usage_records"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    user_id: Optional[str] = Column(String(36), nullable=True, index=True)
    project_id: Optional[str] = Column(String(36), nullable=True, index=True)
    resource_type: str = Column(String(100), nullable=False, index=True)  # llm_tokens | training_seconds | storage_bytes | api_requests
    quantity: float = Column(Float, nullable=False)
    unit: str = Column(String(50), nullable=False)
    usage_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False, index=True)


# ================================================================== #
#  11. LEGACY SESSIONS & MESSAGES (100% BACKWARD COMPATIBLE)
# ================================================================== #

class LegacySession(Base):
    """Legacy interactive user session container."""
    __tablename__ = "sessions"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    name: str = Column(String(255), nullable=False, default="Untitled Session")
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now())
    status: str = Column(String(50), default="created")
    current_stage: str = Column(String(100), default="INGEST")
    task_type: Optional[str] = Column(String(50), nullable=True)
    target_column: Optional[str] = Column(String(255), nullable=True)

    messages: list[ConversationMessage] = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """Chat message history."""
    __tablename__ = "conversation_messages"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    session_id: str = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: str = Column(String(20), nullable=False)
    content: str = Column(Text, nullable=False)
    msg_metadata: Optional[dict] = Column("metadata", JSON, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now())

    session: LegacySession = relationship("LegacySession", back_populates="messages")


# ================================================================== #
#  12. REAL-TIME DATA, FEATURE STORE, CDC & LIFECYCLE (SECTION 57)
# ================================================================== #

class Organization(Base):
    """Multi-tenant organization boundary."""
    __tablename__ = "organizations"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    name: str = Column(String(255), nullable=False)
    slug: str = Column(String(100), unique=True, nullable=False, index=True)
    plan: str = Column(String(50), default="enterprise", nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class DataSource(Base):
    """External database or stream connection specification."""
    __tablename__ = "data_sources"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    source_type: str = Column(String(50), nullable=False)  # postgresql | mysql | mongodb | sqlserver | snowflake | bigquery | rest_api | webhook | stream
    connection_uri_masked: str = Column(String(512), nullable=False)
    read_only: bool = Column(Boolean, default=True, nullable=False)
    ssl_enabled: bool = Column(Boolean, default=True, nullable=False)
    allowed_schemas: Optional[dict] = Column(JSON, nullable=True)
    allowed_tables: Optional[dict] = Column(JSON, nullable=True)
    query_row_limit: int = Column(Integer, default=50000, nullable=False)
    status: str = Column(String(50), default="connected", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class DataSourceCredentialsMetadata(Base):
    """Encrypted credential vault metadata for external databases."""
    __tablename__ = "data_source_credentials_metadata"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    data_source_id: str = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    key_vault_reference: str = Column(String(255), nullable=False)
    encryption_algorithm: str = Column(String(50), default="AES-256-GCM", nullable=False)
    last_rotated_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class FeatureSet(Base):
    """Feature store grouping entity."""
    __tablename__ = "feature_sets"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    project_id: str = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    entity_key: str = Column(String(100), nullable=False)  # e.g., customer_id, transaction_id
    version: str = Column(String(50), default="1.0.0", nullable=False)
    freshness_sla_seconds: int = Column(Integer, default=3600, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class ModelArtifact(Base):
    """Packaged model binary, ONNX, joblib, and deployment runtime artifacts."""
    __tablename__ = "model_artifacts"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    model_version_id: str = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    format: str = Column(String(50), nullable=False)  # onnx | joblib | safetensors | pickle
    storage_path: str = Column(String(1024), nullable=False)
    checksum_sha256: str = Column(String(64), nullable=False)
    size_bytes: int = Column(BigInteger, default=0, nullable=False)
    is_production_ready: bool = Column(Boolean, default=False, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class PredictionResult(Base):
    """Recorded inference outcomes and optional ground truth association."""
    __tablename__ = "prediction_results"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    prediction_request_id: str = Column(String(36), ForeignKey("prediction_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction: dict = Column(JSON, nullable=False)
    probability: Optional[dict] = Column(JSON, nullable=True)
    ground_truth: Optional[dict] = Column(JSON, nullable=True)
    ground_truth_received_at: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class OptimizationRun(Base):
    """Detailed hyperparameter and feature optimization trial series."""
    __tablename__ = "optimization_runs"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    experiment_id: str = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    study_name: str = Column(String(255), nullable=False)
    objective_metric: str = Column(String(100), nullable=False)
    direction: str = Column(String(20), default="maximize", nullable=False)
    best_score: Optional[float] = Column(Float, nullable=True)
    best_params: Optional[dict] = Column(JSON, nullable=True)
    total_trials: int = Column(Integer, default=0, nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class RetrainingEvent(Base):
    """Audit records for automated continuous retraining runs."""
    __tablename__ = "retraining_events"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    model_id: str = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_reason: str = Column(String(100), nullable=False)  # drift_detected | performance_drop | manual | schedule
    drift_score: Optional[float] = Column(Float, nullable=True)
    previous_version_id: Optional[str] = Column(String(36), nullable=True)
    candidate_version_id: Optional[str] = Column(String(36), nullable=True)
    status: str = Column(String(50), default="in_progress", nullable=False)  # in_progress | promoted | rejected | failed
    decision: Optional[str] = Column(String(100), nullable=True)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)


class OnlineLearningEvent(Base):
    """Audit records for streaming/incremental partial_fit learning events."""
    __tablename__ = "online_learning_events"

    id: str = Column(String(36), primary_key=True, default=_uuid)
    model_id: str = Column(String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_size: int = Column(Integer, nullable=False)
    pre_update_metric: Optional[float] = Column(Float, nullable=True)
    post_update_metric: Optional[float] = Column(Float, nullable=True)
    is_promoted: bool = Column(Boolean, default=True, nullable=False)
    validation_status: str = Column(String(50), default="accepted", nullable=False)
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
