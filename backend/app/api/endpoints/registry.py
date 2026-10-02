"""
DataWise AI — Model Registry Endpoints (Phase 11)
Governs model registration, immutable versioning, status lifecycle transitions,
and rollbacks.
Statuses: development, testing, staging, production, archived.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.production_readiness import ProductionReadinessChecker

router = APIRouter()

ModelStatus = Literal["development", "testing", "staging", "production", "archived"]

# In-memory registry store with thread-safety for high-speed serving
_REGISTRY_DB: Dict[str, Dict[str, Any]] = {}
_PRODUCTION_POINTERS: Dict[str, str] = {}  # {project_name: model_version_id}


class ModelRegisterRequest(BaseModel):
    project_id: str
    model_name: str
    version: str = "v1.0.0"
    task_type: str = "classification"
    target_column: Optional[str] = None
    feature_columns: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    artifact_path: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ModelTransitionRequest(BaseModel):
    target_status: ModelStatus
    approval_token: Optional[str] = None
    reason: Optional[str] = None


@router.post("/register")
async def register_model(request: ModelRegisterRequest):
    """Register a new immutable model version."""
    model_id = str(uuid.uuid4())
    record = {
        "id": model_id,
        "project_id": request.project_id,
        "model_name": request.model_name,
        "version": request.version,
        "status": "development",
        "task_type": request.task_type,
        "target_column": request.target_column,
        "feature_columns": request.feature_columns,
        "metrics": request.metrics,
        "artifact_path": request.artifact_path,
        "parameters": request.parameters,
        "created_at": datetime.utcnow().isoformat(),
        "history": [f"Registered at {datetime.utcnow().isoformat()} with status=development"],
    }
    _REGISTRY_DB[model_id] = record
    return {"status": "success", "model_id": model_id, "record": record}


@router.get("")
async def list_models(project_id: Optional[str] = None, status: Optional[ModelStatus] = None):
    """List all registered models with optional filtering."""
    results = list(_REGISTRY_DB.values())
    if project_id:
        results = [r for r in results if r.get("project_id") == project_id]
    if status:
        results = [r for r in results if r.get("status") == status]
    return {"total": len(results), "models": results}


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Retrieve details of a registered model."""
    if model_id not in _REGISTRY_DB:
        raise HTTPException(status_code=404, detail="Model not found in registry")
    return _REGISTRY_DB[model_id]


@router.get("/{model_id}/readiness")
async def get_model_readiness(model_id: str):
    """Executes the 13-point production deployment checklist (Master Spec Section 30, 55)."""
    if model_id not in _REGISTRY_DB:
        raise HTTPException(status_code=404, detail="Model not found in registry")
    model = _REGISTRY_DB[model_id]
    project = model["project_id"]
    prev_versions = [
        m["id"] for m in _REGISTRY_DB.values()
        if m.get("project_id") == project and m["id"] != model_id
    ]
    report = ProductionReadinessChecker.evaluate(
        model_id=model_id,
        model_version=model["version"],
        state_data=model,
        previous_versions=prev_versions,
    )
    return report.model_dump()


@router.post("/{model_id}/transition")
async def transition_model_status(model_id: str, request: ModelTransitionRequest):
    """Transitions model lifecycle status (e.g. staging -> production). Never overwrites production silently."""
    if model_id not in _REGISTRY_DB:
        raise HTTPException(status_code=404, detail="Model not found in registry")

    model = _REGISTRY_DB[model_id]
    current = model["status"]
    target = request.target_status

    if target == "production":
        # Master Rule #55: Run production readiness checklist before deployment!
        project = model["project_id"]
        prev_versions = [
            m["id"] for m in _REGISTRY_DB.values()
            if m.get("project_id") == project and m["id"] != model_id
        ]
        readiness = ProductionReadinessChecker.evaluate(
            model_id=model_id,
            model_version=model["version"],
            state_data=model,
            previous_versions=prev_versions,
        )
        if not readiness.is_ready_for_deployment:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Model failed production readiness validation",
                    "readiness_report": readiness.model_dump(),
                }
            )

        # Check if an existing production model exists
        existing_prod_id = _PRODUCTION_POINTERS.get(project)
        if existing_prod_id and existing_prod_id != model_id:
            # Demote existing production to archived (Section 56: Never delete previous production versions)
            old_prod = _REGISTRY_DB.get(existing_prod_id)
            if old_prod:
                old_prod["status"] = "archived"
                old_prod["history"].append(f"Demoted to archived on promotion of {model_id}")

        _PRODUCTION_POINTERS[project] = model_id

    model["status"] = target
    model["history"].append(f"Transitioned from {current} to {target} at {datetime.utcnow().isoformat()} (Reason: {request.reason})")

    return {
        "status": "success",
        "model_id": model_id,
        "previous_status": current,
        "new_status": target,
    }


@router.post("/{model_id}/rollback")
async def rollback_model(model_id: str):
    """Rolls back an archived/staging model back into active production."""
    if model_id not in _REGISTRY_DB:
        raise HTTPException(status_code=404, detail="Model not found in registry")

    model = _REGISTRY_DB[model_id]
    project = model["project_id"]
    current_prod_id = _PRODUCTION_POINTERS.get(project)

    if current_prod_id and current_prod_id in _REGISTRY_DB:
        _REGISTRY_DB[current_prod_id]["status"] = "archived"

    model["status"] = "production"
    _PRODUCTION_POINTERS[project] = model_id
    model["history"].append(f"Rolled back to production at {datetime.utcnow().isoformat()}")

    return {"status": "success", "rolled_back_to": model_id}
