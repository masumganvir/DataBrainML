"""
DataWise AI — Advanced Analysis Endpoints (Steps 10-16)

Endpoints for:
  - Feature Engineering
  - Feature Selection
  - Target Detection & ML Task Classification
  - Leakage Detection
  - Pipeline Building
  - ML Recommendations
  - ML Readiness Assessment
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coordinator import multi_agent_coordinator
from app.models.database import get_db
from app.models.db_models import Artifact, Dataset, Session
from app.state.data_science_state import DataScienceState
from app.tools.feature_engineering import FeatureEngineer
from app.tools.feature_selection import FeatureSelector
from app.tools.leakage import LeakageDetector
from app.tools.ml_recommender import MLRecommender, compute_ml_readiness
from app.tools.pipeline_builder import PipelineBuilder
from app.tools.storage import storage_manager
from app.tools.target_detector import TargetDetector

router = APIRouter()



# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

async def _get_session_and_dataset(
    session_id: str, db: AsyncSession
) -> tuple[Session, Dataset, pd.DataFrame]:
    sess_q = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_q.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    ds_q = await db.execute(
        select(Dataset)
        .where(Dataset.session_id == session_id)
        .order_by(Dataset.created_at.desc())
    )
    dataset = ds_q.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset found for this session.")

    try:
        df = storage_manager.load_dataframe(dataset.file_path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {exc}") from exc

    return session, dataset, df


# ------------------------------------------------------------------ #
#  Schemas
# ------------------------------------------------------------------ #

class TargetConfirmRequest(BaseModel):
    target_column: str
    task_type: Optional[str] = None


class FeatureEngineeringApplyRequest(BaseModel):
    operations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of operation dicts returned by the recommendation endpoint"
    )


class MLRecommendRequest(BaseModel):
    task_type: str = "classification"
    target_column: Optional[str] = None


# ------------------------------------------------------------------ #
#  Feature Engineering
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/feature-engineering/recommend",
    summary="Recommend feature engineering operations",
)
async def recommend_feature_engineering(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    target = session.target_column

    engineer = FeatureEngineer(df, target_column=target, task_type=session.task_type)
    result = engineer.recommend_features()

    session.current_stage = "FEATURE_ENGINEERING"
    await db.commit()

    return {
        "session_id": session_id,
        "target_column": target,
        **result,
    }


@router.post(
    "/{session_id}/feature-engineering/apply",
    summary="Apply approved feature engineering operations",
)
async def apply_feature_engineering(
    session_id: str,
    payload: FeatureEngineeringApplyRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    target = session.target_column

    engineer = FeatureEngineer(df, target_column=target, task_type=session.task_type)
    augmented_df = engineer.apply_features(payload.operations)

    # Save augmented dataset
    new_path = storage_manager.save_processed_dataframe(
        augmented_df, session_id, version="feature_engineered"
    )
    new_cols = [c for c in augmented_df.columns if c not in df.columns]

    session.current_stage = "FEATURE_SELECTION"
    await db.commit()

    return {
        "session_id": session_id,
        "original_columns": len(df.columns),
        "augmented_columns": len(augmented_df.columns),
        "new_features": new_cols,
        "saved_path": new_path,
        "next_stage": "FEATURE_SELECTION",
    }


# ------------------------------------------------------------------ #
#  Feature Selection
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/feature-selection",
    summary="Run feature selection and get recommendations",
)
async def run_feature_selection(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    target = session.target_column

    selector = FeatureSelector(df, target_column=target, task_type=session.task_type)
    result = selector.run_all()

    session.current_stage = "FEATURE_SELECTION"
    await db.commit()

    return {
        "session_id": session_id,
        "target_column": target,
        **result,
    }


# ------------------------------------------------------------------ #
#  Target Detection
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/target/detect",
    summary="Auto-detect target column candidates",
)
async def detect_target(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)

    detector = TargetDetector(df)
    result = detector.detect()

    return {
        "session_id": session_id,
        **result,
    }


@router.post(
    "/{session_id}/target/confirm",
    summary="Confirm target column and task type",
)
async def confirm_target(
    session_id: str,
    payload: TargetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)

    detector = TargetDetector(df)
    analysis = detector.analyse_target(payload.target_column, payload.task_type)

    session.target_column = payload.target_column
    session.task_type = analysis.get("task_type", payload.task_type)
    session.current_stage = "LEAKAGE_CHECK"
    await db.commit()

    return {
        "session_id": session_id,
        "confirmed_target": payload.target_column,
        "confirmed_task_type": session.task_type,
        **analysis,
    }


# ------------------------------------------------------------------ #
#  Leakage Detection
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/leakage",
    summary="Detect data leakage risks in the dataset",
)
async def detect_leakage(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    target = session.target_column

    detector = LeakageDetector(df, target_column=target, task_type=session.task_type)
    result = detector.detect()

    session.current_stage = "PIPELINE_BUILDING"
    await db.commit()

    return {
        "session_id": session_id,
        "target_column": target,
        **result,
    }


# ------------------------------------------------------------------ #
#  Pipeline Building
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/pipeline/build",
    summary="Generate sklearn pipeline definition and code",
)
async def build_pipeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    target = session.target_column

    # Load analysis summaries from dataset
    encoding_plan = (dataset.profile_summary or {}).get("encoding_plan", [])
    scaling_plan = (dataset.profile_summary or {}).get("scaling_plan", [])
    transformation_plan = (dataset.profile_summary or {}).get("transformation_plan", [])

    builder = PipelineBuilder(
        df,
        target_column=target,
        task_type=session.task_type,
        encoding_plan=encoding_plan,
        scaling_plan=scaling_plan,
        transformation_plan=transformation_plan,
    )
    definition = builder.build()
    code = definition.get("generated_code", "")

    # Persist code as artifact
    import uuid, os

    artifact_id = str(uuid.uuid4())
    artifact_dir = storage_manager.get_artifacts_dir(session_id)
    os.makedirs(artifact_dir, exist_ok=True)
    code_path = os.path.join(artifact_dir, f"pipeline_{artifact_id}.py")
    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    artifact = Artifact(
        session_id=session_id,
        artifact_type="code",
        name="sklearn_pipeline.py",
        description="Auto-generated sklearn preprocessing pipeline and model training code",
        file_path=code_path,
        file_format="py",
        file_size_bytes=len(code.encode()),
    )
    db.add(artifact)

    session.current_stage = "ML_RECOMMENDATION"
    await db.commit()
    await db.refresh(artifact)

    return {
        "session_id": session_id,
        "artifact_id": artifact.id,
        "pipeline_definition": {k: v for k, v in definition.items() if k != "generated_code"},
        "generated_code": code,
    }


# ------------------------------------------------------------------ #
#  ML Recommendations
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/ml/recommend",
    summary="Get ML algorithm recommendations and readiness score",
)
async def get_ml_recommendations(
    session_id: str,
    payload: MLRecommendRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)

    quality = dataset.quality_summary or {}
    missing_reports = quality.get("missing_reports", [])
    avg_missing = sum(r.get("missing_pct", 0) for r in missing_reports) / max(len(missing_reports), 1)
    high_severity = sum(1 for r in missing_reports if r.get("severity") in ("HIGH", "CRITICAL"))
    dup_pct = quality.get("duplicates", {}).get("duplicate_pct", 0.0)

    task = payload.task_type or session.task_type or "classification"
    target = payload.target_column or session.target_column

    recommender = MLRecommender(
        task_type=task,
        row_count=dataset.row_count or len(df),
        col_count=dataset.column_count or len(df.columns),
        is_imbalanced=False,  # Will be updated after target analysis
        missing_pct_avg=avg_missing,
        high_severity_missing=high_severity,
        duplicate_pct=float(dup_pct),
        outlier_severity="mild",
        leakage_warnings=0,
        has_target=bool(target),
    )
    result = recommender.recommend()

    session.current_stage = "COMPLETE"
    session.task_type = task
    if target:
        session.target_column = target
    await db.commit()

    return {
        "session_id": session_id,
        "task_type": task,
        "target_column": target,
        **result,
    }


# ------------------------------------------------------------------ #
#  ML Readiness Score
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/ml/readiness",
    summary="Compute ML readiness score for the current dataset",
)
async def get_ml_readiness(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)

    quality = dataset.quality_summary or {}
    missing_reports = quality.get("missing_reports", [])
    avg_missing = sum(r.get("missing_pct", 0) for r in missing_reports) / max(len(missing_reports), 1)
    high_severity = sum(1 for r in missing_reports if r.get("severity") in ("HIGH", "CRITICAL"))
    dup_pct = quality.get("duplicates", {}).get("duplicate_pct", 0.0)

    readiness = compute_ml_readiness(
        row_count=dataset.row_count or len(df),
        col_count=dataset.column_count or len(df.columns),
        missing_pct_avg=avg_missing,
        high_severity_missing=high_severity,
        duplicate_pct=float(dup_pct),
        outlier_severity="mild",
        leakage_warnings=0,
        has_target=bool(session.target_column),
    )

    return {
        "session_id": session_id,
        **readiness,
        "dataset_stats": {
            "rows": dataset.row_count,
            "columns": dataset.column_count,
            "avg_missing_pct": round(avg_missing, 2),
            "high_severity_missing_cols": high_severity,
            "duplicate_pct": dup_pct,
            "target_defined": bool(session.target_column),
        },
    }


# ------------------------------------------------------------------ #
#  State Cache & Helper
# ------------------------------------------------------------------ #

_session_state_cache: Dict[str, DataScienceState] = {}


def _get_or_create_state(
    session_id: str,
    session: Session,
    dataset: Dataset,
    df: pd.DataFrame,
) -> DataScienceState:
    """Retrieve or initialize in-memory state for the active analysis session."""
    if session_id in _session_state_cache:
        state = _session_state_cache[session_id]
        state["dataset_path_analysis"] = dataset.file_path
        state["dataset_path_original"] = dataset.file_path
        if session.target_column:
            state["target_column"] = session.target_column
        if session.task_type:
            state["task_type"] = session.task_type
        return state

    state: DataScienceState = {
        "session_id": session_id,
        "dataset_path_original": dataset.file_path,
        "dataset_path_analysis": dataset.file_path,
        "target_column": session.target_column,
        "task_type": session.task_type,
        "dataset_domain": None,
        "prediction_objective": None,
        "execution_mode": "guided",
        "current_stage": session.current_stage or "INGEST",
        "completed_stages": [],
        "errors": [],
        "user_decisions": [],
        "outlier_decisions": [],
        "trained_models": [],
        "decision_log": [],
    }
    _session_state_cache[session_id] = state
    return state


# ------------------------------------------------------------------ #
#  Domain & Objective Context
# ------------------------------------------------------------------ #

class SessionContextRequest(BaseModel):
    dataset_domain: Optional[str] = Field(
        None,
        description="e.g. banking, healthcare, ecommerce, cybersecurity, manufacturing, finance"
    )
    prediction_objective: Optional[str] = Field(
        None,
        description="e.g. fraud, customer churn, house price, disease classification, credit risk"
    )
    execution_mode: Optional[str] = Field(
        "guided",
        description="'guided' asks before important decisions; 'autonomous' uses analytical safeguards"
    )


@router.post(
    "/{session_id}/context",
    summary="Set dataset domain, ML objective, and execution mode",
)
async def update_session_context(
    session_id: str,
    payload: SessionContextRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    if payload.dataset_domain is not None:
        state["dataset_domain"] = payload.dataset_domain
    if payload.prediction_objective is not None:
        state["prediction_objective"] = payload.prediction_objective
    if payload.execution_mode is not None:
        state["execution_mode"] = payload.execution_mode

    _session_state_cache[session_id] = state

    return {
        "session_id": session_id,
        "dataset_domain": state.get("dataset_domain"),
        "prediction_objective": state.get("prediction_objective"),
        "execution_mode": state.get("execution_mode"),
        "message": "Domain and objective context updated successfully.",
    }


# ------------------------------------------------------------------ #
#  Automated ML Model Training & Evaluation
# ------------------------------------------------------------------ #

class TrainModelsRequest(BaseModel):
    target_column: Optional[str] = None
    task_type: Optional[str] = None
    primary_metric: Optional[str] = None
    candidate_models: Optional[List[str]] = None
    cv_folds: int = Field(5, ge=2, le=10)
    test_size: float = Field(0.2, ge=0.05, le=0.4)


@router.post(
    "/{session_id}/ml/train",
    summary="Train candidate ML models with leak-free cross-validation",
)
async def train_models_endpoint(
    session_id: str,
    payload: TrainModelsRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    # Apply request parameters
    target = payload.target_column or session.target_column or state.get("target_column")
    if not target:
        raise HTTPException(
            status_code=400,
            detail="A target column is required for model training. Please specify target_column.",
        )
    state["target_column"] = target
    session.target_column = target

    if payload.task_type:
        state["task_type"] = payload.task_type
        session.task_type = payload.task_type
    elif not state.get("task_type"):
        state["task_type"] = "classification"

    if payload.primary_metric:
        state["primary_metric"] = payload.primary_metric

    # 1. Run TrainingAgent (train/test partition, CV on train only, candidate models)
    state = multi_agent_coordinator.training_agent.run(state)

    # 2. Run EvaluationAgent (covariate shift KS-test & 8-point production readiness audit)
    state = multi_agent_coordinator.evaluation_agent.run(state)

    # 3. Run ExplainabilityAgent (feature importances & permutation importances)
    state = multi_agent_coordinator.explainability_agent.run(state)

    session.current_stage = "TRAINING"
    await db.commit()
    _session_state_cache[session_id] = state

    return {
        "session_id": session_id,
        "task_type": state.get("task_type"),
        "target_column": state.get("target_column"),
        "primary_metric": state.get("primary_metric"),
        "cv_strategy": state.get("cv_strategy"),
        "selected_final_model": state.get("selected_final_model"),
        "models": state.get("trained_models", []),
        "selection_rationale": (
            state["trained_models"][0].get("champion_rationale")
            if state.get("trained_models")
            else "Champion selected by validation performance."
        ),
        "production_readiness": state.get("production_readiness"),
        "dataset_shift": state.get("dataset_shift_report"),
        "feature_importance": (
            state.get("model_explainability", {}).get("feature_importance", {})
            if state.get("model_explainability")
            else {}
        ),
        "limitations": (
            state.get("production_readiness", {}).get("limitations", [])
            if state.get("production_readiness")
            else []
        ),
    }


# ------------------------------------------------------------------ #
#  Model Comparison Dashboard
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/ml/comparison",
    summary="Get interactive model comparison table and evaluation details",
)
async def get_model_comparison(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    models = state.get("trained_models", [])
    if not models:
        return {
            "session_id": session_id,
            "models": [],
            "trained": False,
            "message": "No models trained yet for this session. Use POST /ml/train first.",
        }

    return {
        "session_id": session_id,
        "trained": True,
        "task_type": state.get("task_type"),
        "target_column": state.get("target_column"),
        "primary_metric": state.get("primary_metric"),
        "cv_strategy": state.get("cv_strategy"),
        "selected_final_model": state.get("selected_final_model"),
        "models": models,
        "production_readiness": state.get("production_readiness"),
        "dataset_shift": state.get("dataset_shift_report"),
        "model_explainability": state.get("model_explainability"),
    }


class SelectModelRequest(BaseModel):
    model_name: str
    rationale: Optional[str] = None


@router.post(
    "/{session_id}/ml/select-model",
    summary="Manually select or override the champion model",
)
async def select_champion_model(
    session_id: str,
    payload: SelectModelRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    models = state.get("trained_models", [])
    matched = next((m for m in models if m.get("model_name") == payload.model_name), None)
    if not matched:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{payload.model_name}' not found among trained models.",
        )

    # Update champion flag
    for m in models:
        m["is_champion"] = m.get("model_name") == payload.model_name

    state["selected_final_model"] = payload.model_name
    _session_state_cache[session_id] = state

    return {
        "session_id": session_id,
        "selected_final_model": payload.model_name,
        "rationale": payload.rationale or f"User manually selected {payload.model_name} as final model.",
        "message": f"Champion model set to {payload.model_name}.",
    }


# ------------------------------------------------------------------ #
#  Jupyter Notebook Generation & Download
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/notebook/generate",
    summary="Generate standalone 24-section Jupyter Notebook (.ipynb)",
)
async def generate_notebook_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    state = multi_agent_coordinator.notebook_agent.run(state)
    nb_path = state.get("notebook_path")
    if not nb_path or not Path(nb_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate Jupyter Notebook.")

    # Record in database artifacts table
    artifact = Artifact(
        id=str(uuid.uuid4()),
        session_id=session_id,
        name="Executable Data Science & AutoML Notebook",
        description="Comprehensive 24-section Jupyter Notebook (.ipynb) with genuine Python cells",
        artifact_type="notebook",
        file_path=nb_path,
        file_format="ipynb",
        file_size_bytes=Path(nb_path).stat().st_size,
    )
    db.add(artifact)
    await db.commit()

    _session_state_cache[session_id] = state

    return {
        "session_id": session_id,
        "notebook_path": nb_path,
        "filename": Path(nb_path).name,
        "download_url": f"/api/v1/sessions/{session_id}/notebook/download",
        "file_size_bytes": Path(nb_path).stat().st_size,
        "message": "Jupyter Notebook generated successfully.",
    }


@router.get(
    "/{session_id}/notebook/download",
    summary="Download generated Jupyter Notebook (.ipynb)",
)
async def download_notebook(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    nb_path = state.get("notebook_path")
    if not nb_path or not Path(nb_path).exists():
        # Check DB artifact fallback
        art_q = await db.execute(
            select(Artifact)
            .where(Artifact.session_id == session_id, Artifact.artifact_type == "notebook")
            .order_by(Artifact.created_at.desc())
        )
        art = art_q.scalars().first()
        if art and Path(art.file_path).exists():
            nb_path = art.file_path
        else:
            # Generate on-demand
            state = multi_agent_coordinator.notebook_agent.run(state)
            nb_path = state.get("notebook_path")

    if not nb_path or not Path(nb_path).exists():
        raise HTTPException(status_code=404, detail="Notebook artifact not found.")

    return FileResponse(
        path=nb_path,
        filename=Path(nb_path).name,
        media_type="application/x-ipynb+json",
        headers={"Content-Disposition": f'attachment; filename="{Path(nb_path).name}"'},
    )


# ------------------------------------------------------------------ #
#  Artifacts Packaging & Downloads (ZIP, Model, Code)
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/artifacts/package",
    summary="Serialize pipeline and package all project deliverables into a ZIP bundle",
)
async def package_artifacts_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    # 1. Ensure models and notebook exist
    if not state.get("trained_models"):
        state = multi_agent_coordinator.training_agent.run(state)
    if not state.get("notebook_path") or not Path(state["notebook_path"]).exists():
        state = multi_agent_coordinator.notebook_agent.run(state)

    # 2. Run ArtifactManagerAgent
    state = multi_agent_coordinator.artifact_agent.run(state)
    bundle_path = state.get("project_bundle_path")
    if not bundle_path or not Path(bundle_path).exists():
        raise HTTPException(status_code=500, detail="Failed to package project artifacts.")

    # Record bundle artifact in DB
    artifact = Artifact(
        id=str(uuid.uuid4()),
        session_id=session_id,
        name="DataWise AI Complete Deliverable Package (ZIP)",
        description="Packaged model, notebook, reports, inference code, and documentation",
        artifact_type="bundle",
        file_path=bundle_path,
        file_format="zip",
        file_size_bytes=Path(bundle_path).stat().st_size,
    )
    db.add(artifact)
    await db.commit()

    _session_state_cache[session_id] = state

    return {
        "session_id": session_id,
        "bundle_path": bundle_path,
        "filename": Path(bundle_path).name,
        "zip_size_bytes": Path(bundle_path).stat().st_size,
        "download_url": f"/api/v1/sessions/{session_id}/artifacts/download-bundle",
        "final_pipeline_path": state.get("final_pipeline_path"),
        "model_metadata_path": state.get("model_metadata_path"),
        "notebook_path": state.get("notebook_path"),
        "message": "Complete project artifact package generated successfully.",
    }


@router.get(
    "/{session_id}/artifacts/download-bundle",
    summary="Download complete DataWise project bundle (.zip)",
)
async def download_bundle(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    bundle_path = state.get("project_bundle_path")
    if not bundle_path or not Path(bundle_path).exists():
        # Check DB artifact
        art_q = await db.execute(
            select(Artifact)
            .where(Artifact.session_id == session_id, Artifact.artifact_type == "bundle")
            .order_by(Artifact.created_at.desc())
        )
        art = art_q.scalars().first()
        if art and Path(art.file_path).exists():
            bundle_path = art.file_path
        else:
            state = multi_agent_coordinator.artifact_agent.run(state)
            bundle_path = state.get("project_bundle_path")

    if not bundle_path or not Path(bundle_path).exists():
        raise HTTPException(status_code=404, detail="Artifact bundle ZIP not found.")

    return FileResponse(
        path=bundle_path,
        filename=Path(bundle_path).name,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{Path(bundle_path).name}"'},
    )


@router.get(
    "/{session_id}/model/download",
    summary="Download serialized production pipeline (.joblib)",
)
async def download_model_pipeline(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    model_path = state.get("final_pipeline_path")
    if not model_path or not Path(model_path).exists():
        state = multi_agent_coordinator.artifact_agent.run(state)
        model_path = state.get("final_pipeline_path")

    if not model_path or not Path(model_path).exists():
        raise HTTPException(status_code=404, detail="Serialized model pipeline (.joblib) not found.")

    return FileResponse(
        path=model_path,
        filename=Path(model_path).name,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{Path(model_path).name}"'},
    )


# ------------------------------------------------------------------ #
#  Inference & Prediction Endpoints
# ------------------------------------------------------------------ #

class PredictRequest(BaseModel):
    features: Dict[str, Any]


class BatchPredictResponse(BaseModel):
    total_records: int
    predictions: List[Any]
    probabilities: Optional[List[List[float]]] = None


@router.get(
    "/{session_id}/model/info",
    summary="Get deployed champion model metadata and input schema",
)
async def get_model_info(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    champion = state.get("selected_final_model")
    target = state.get("target_column")
    task = state.get("ml_task_type", "classification")

    # Features expected by pipeline
    feature_cols = [c for c in df.columns if c != target] if target else list(df.columns)

    return {
        "session_id": session_id,
        "champion_model": champion,
        "target_column": target,
        "task_type": task,
        "features": feature_cols,
        "primary_metric": state.get("primary_metric"),
        "cv_score": state.get("evaluation_results", {}).get("cv_score_mean"),
        "test_score": state.get("evaluation_results", {}).get("test_score"),
    }


@router.post(
    "/{session_id}/model/predict",
    summary="Make real-time prediction on a single record",
)
async def predict_single(
    session_id: str,
    payload: PredictRequest,
    db: AsyncSession = Depends(get_db),
):
    import joblib
    from app.tools.model_trainer import _pipeline_cache

    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    pipeline = _pipeline_cache.get(session_id)
    if pipeline is None:
        model_path = state.get("final_pipeline_path")
        if not model_path or not Path(model_path).exists():
            import glob
            matches = glob.glob(f"artifacts/{session_id}/**/final_model.joblib", recursive=True)
            if matches:
                model_path = matches[0]
        if model_path and Path(model_path).exists():
            pipeline = joblib.load(model_path)

    if pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="No trained model found for this session. Please train models first.",
        )

    input_df = pd.DataFrame([payload.features])
    try:
        raw_pred = pipeline.predict(input_df)[0]
        pred = raw_pred.item() if hasattr(raw_pred, "item") else raw_pred
        probs = None
        if hasattr(pipeline, "predict_proba"):
            try:
                raw_probs = pipeline.predict_proba(input_df)[0]
                probs = [float(p) for p in raw_probs]
            except Exception:
                probs = None

        return {
            "session_id": session_id,
            "prediction": pred,
            "probabilities": probs,
            "model_name": state.get("selected_final_model"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@router.post(
    "/{session_id}/model/predict-batch",
    response_model=BatchPredictResponse,
    summary="Make batch predictions from uploaded CSV",
)
async def predict_batch(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    import io
    import joblib
    from app.tools.model_trainer import _pipeline_cache

    session, dataset, df = await _get_session_and_dataset(session_id, db)
    state = _get_or_create_state(session_id, session, dataset, df)

    pipeline = _pipeline_cache.get(session_id)
    if pipeline is None:
        model_path = state.get("final_pipeline_path")
        if not model_path or not Path(model_path).exists():
            import glob
            matches = glob.glob(f"artifacts/{session_id}/**/final_model.joblib", recursive=True)
            if matches:
                model_path = matches[0]
        if model_path and Path(model_path).exists():
            pipeline = joblib.load(model_path)

    if pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="No trained model found for this session. Please train models first.",
        )

    content = await file.read()
    try:
        batch_df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")

    target = state.get("target_column")
    if target and target in batch_df.columns:
        batch_df = batch_df.drop(columns=[target])

    try:
        raw_preds = pipeline.predict(batch_df)
        preds = [p.item() if hasattr(p, "item") else p for p in raw_preds]
        probs = None
        if hasattr(pipeline, "predict_proba"):
            try:
                raw_probs = pipeline.predict_proba(batch_df)
                probs = [[float(v) for v in row] for row in raw_probs]
            except Exception:
                probs = None

        return BatchPredictResponse(
            total_records=len(batch_df),
            predictions=preds,
            probabilities=probs,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch prediction error: {str(e)}")

