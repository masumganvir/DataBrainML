"""
DataWise AI — Report & Roadmap Export Endpoints (Step 20)

Provides:
  - GET  /sessions/{session_id}/reports/markdown — Analytical Markdown report
  - GET  /sessions/{session_id}/reports/html     — Standalone executive HTML report
  - GET  /sessions/{session_id}/reports/roadmap  — Enterprise ML roadmap
  - POST /sessions/{session_id}/reports/generate — Generate and save all report artifacts
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import Artifact, Dataset, Session
from app.reports.report_generator import (
    generate_html_report,
    generate_markdown_report,
    generate_ml_roadmap,
)
from app.state.data_science_state import DataScienceState
from app.tools.correlations import CorrelationAnalyzer
from app.tools.distributions import DistributionAnalyzer
from app.tools.ml_recommender import MLRecommender, compute_ml_readiness
from app.tools.outliers import OutlierAnalyzer
from app.tools.profiler import DatasetProfiler
from app.tools.quality import QualityAnalyzer
from app.tools.storage import storage_manager
from app.tools.target_detector import TargetDetector

router = APIRouter()


async def _reconstruct_state_from_session(
    session_id: str, db: AsyncSession
) -> DataScienceState:
    """Builds an enriched DataScienceState from stored dataset and artifacts."""
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {exc}")

    # Run core analyzers to assemble up-to-date state
    profiler = DatasetProfiler()
    profile = profiler.profile(df)

    quality = QualityAnalyzer()
    missing_report = quality.analyze_missing(df)
    dup_report = quality.analyze_duplicates(df)

    outlier_analyzer = OutlierAnalyzer()
    num_cols = profile.get("numerical_columns", [])
    outlier_report = outlier_analyzer.analyze_dataframe(df, num_cols)

    target_detector = TargetDetector()
    target_info = target_detector.detect_target_candidates(df)
    target_col = target_info.get("primary_candidate")
    task_type = target_info.get("task_type", "classification")

    # ML Readiness and recommendations
    ml_rec = MLRecommender()
    readiness = compute_ml_readiness(
        df=df,
        missing_report=missing_report,
        outlier_report=outlier_report,
        target_column=target_col,
        task_type=task_type,
    )

    models = ml_rec.recommend_models(
        task_type=task_type,
        n_samples=len(df),
        n_features=len(df.columns),
        has_categorical=bool(profile.get("categorical_columns")),
    )

    state: DataScienceState = {
        "session_id": session_id,
        "dataset_id": str(dataset.id),
        "dataset_path_original": dataset.file_path,
        "dataset_metadata": {
            "filename": dataset.filename,
            "row_count": len(df),
            "col_count": len(df.columns),
            "size_bytes": dataset.file_size_bytes or 0,
        },
        "numerical_columns": profile.get("numerical_columns", []),
        "categorical_columns": profile.get("categorical_columns", []),
        "datetime_columns": profile.get("datetime_columns", []),
        "column_profiles": profile.get("column_profiles", []),
        "missing_value_report": missing_report,
        "duplicate_report": dup_report,
        "outlier_report": outlier_report,
        "target_column": target_col,
        "task_type": task_type,
        "ml_readiness_score": readiness.get("score"),
        "ml_readiness_level": readiness.get("level"),
        "ml_readiness_report": readiness,
        "model_recommendations": models,
    }
    return state


@router.get(
    "/sessions/{session_id}/reports/markdown",
    summary="Get Markdown analysis report",
    response_class=Response,
)
async def get_markdown_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    state = await _reconstruct_state_from_session(session_id, db)
    md_content = generate_markdown_report(state)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="datawise_report_{session_id[:8]}.md"'
        },
    )


@router.get(
    "/sessions/{session_id}/reports/html",
    summary="Get standalone executive HTML report",
    response_class=Response,
)
async def get_html_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    state = await _reconstruct_state_from_session(session_id, db)
    html_content = generate_html_report(state)
    return Response(
        content=html_content,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="datawise_report_{session_id[:8]}.html"'
        },
    )


@router.get(
    "/sessions/{session_id}/reports/roadmap",
    summary="Get Machine Learning project roadmap",
    response_class=Response,
)
async def get_roadmap_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    state = await _reconstruct_state_from_session(session_id, db)
    roadmap_md = generate_ml_roadmap(state)
    return Response(
        content=roadmap_md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="datawise_ml_roadmap_{session_id[:8]}.md"'
        },
    )


@router.post(
    "/sessions/{session_id}/reports/generate",
    summary="Generate and persist all report artifacts",
)
async def generate_and_save_reports(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    state = await _reconstruct_state_from_session(session_id, db)

    md_content = generate_markdown_report(state)
    html_content = generate_html_report(state)
    roadmap_content = generate_ml_roadmap(state)

    # Save to storage
    md_path = storage_manager.save_text(
        content=md_content,
        session_id=session_id,
        filename="analysis_report.md",
        artifact_type="report",
    )
    html_path = storage_manager.save_text(
        content=html_content,
        session_id=session_id,
        filename="analysis_report.html",
        artifact_type="report",
    )
    roadmap_path = storage_manager.save_text(
        content=roadmap_content,
        session_id=session_id,
        filename="ml_roadmap.md",
        artifact_type="report",
    )

    # Record artifacts in database
    artifacts_to_create = [
        Artifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            name="Comprehensive Analysis Report (Markdown)",
            artifact_type="report",
            file_path=md_path,
            mime_type="text/markdown",
        ),
        Artifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            name="Executive Analysis Report (HTML)",
            artifact_type="report",
            file_path=html_path,
            mime_type="text/html",
        ),
        Artifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            name="Enterprise ML Project Roadmap",
            artifact_type="report",
            file_path=roadmap_path,
            mime_type="text/markdown",
        ),
    ]

    for art in artifacts_to_create:
        db.add(art)
    await db.commit()

    return {
        "success": True,
        "session_id": session_id,
        "reports": {
            "markdown": f"/api/v1/sessions/{session_id}/reports/markdown",
            "html": f"/api/v1/sessions/{session_id}/reports/html",
            "roadmap": f"/api/v1/sessions/{session_id}/reports/roadmap",
        },
    }
