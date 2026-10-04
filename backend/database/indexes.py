"""
DataWise AI — Database Indexes & Optimization
Implements Prompt Section 35:
- Ensures indexes exist on owner_id, project_id, run_id, model_id, etc.
- Prevents redundant full-table scans.
"""

from __future__ import annotations

from typing import List
from sqlalchemy import Index
from app.db.models.entities import (
    User,
    Project,
    DatasetEntity,
    DatasetVersion,
    ExperimentRun,
    ArtifactEntity,
    ModelEntity,
    ModelVersion,
    PredictionRequest,
    AuditLog,
)

CRITICAL_INDEXES = [
    # Users
    Index("idx_users_email", User.email),
    Index("idx_users_role", User.role),
    
    # Projects
    Index("idx_projects_owner_created", Project.user_id, Project.created_at.desc()),
    Index("idx_projects_status", Project.status),

    # Datasets
    Index("idx_datasets_project_id", DatasetEntity.project_id),
    Index("idx_datasets_sha256", DatasetEntity.sha256),

    # Runs
    Index("idx_runs_project_id", ExperimentRun.project_id),
    Index("idx_runs_created_at", ExperimentRun.created_at.desc()),

    # Artifacts
    Index("idx_artifacts_project_run", ArtifactEntity.project_id, ArtifactEntity.run_id),
    Index("idx_artifacts_type", ArtifactEntity.artifact_type),

    # Models & Versions
    Index("idx_models_project", ModelEntity.project_id),
    Index("idx_model_versions_model", ModelVersion.model_id),

    # Predictions
    Index("idx_predictions_model_version", PredictionRequest.model_version_id),

    # Audit Logs
    Index("idx_audit_logs_user_ts", AuditLog.user_id, AuditLog.created_at.desc()),
]


def get_required_indexes() -> List[Index]:
    """Returns list of critical indexes for database migration and verification."""
    return CRITICAL_INDEXES
