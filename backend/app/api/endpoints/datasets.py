"""
DataWise AI — Datasets Endpoints

API for uploading datasets, listing versions, previewing records, and downloading files.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import Dataset, Session
from app.security.file_validator import FileValidationError, validate_uploaded_file
from app.tools.storage import storage_manager

router = APIRouter()


# ------------------------------------------------------------------ #
#  Schemas
# ------------------------------------------------------------------ #

class ColumnSummary(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int


class DatasetResponse(BaseModel):
    id: str
    session_id: str
    version: str
    original_filename: str
    file_format: str
    file_size_bytes: int
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    schema_info: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    total_rows: int
    total_columns: int
    limit: int
    offset: int
    columns: List[ColumnSummary]
    rows: List[Dict[str, Any]]


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/datasets/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a dataset file for analysis",
)
async def upload_dataset(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Validates and stores an uploaded dataset (CSV, XLSX, XLS, JSON).
    Preserves original dataset immutably and registers version 'original'.
    """
    # 1. Verify session exists
    session_query = await db.execute(select(Session).where(Session.id == session_id))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # 2. Read bytes
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 3. Security & format validation
    try:
        validation = validate_uploaded_file(content, file.filename or "dataset.csv")
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": exc.code, "message": exc.message},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(exc)}",
        )

    # 4. Save to persistent storage as 'original' version
    file_path, stored_filename = storage_manager.save_uploaded_bytes(
        session_id=session_id,
        version="original",
        sanitized_filename=validation.filename,
        content=content,
    )

    # 5. Record in database
    schema_info = {
        "columns": validation.columns,
        "encoding": validation.encoding,
        "delimiter": validation.delimiter,
        "warnings": validation.warnings,
    }

    dataset = Dataset(
        session_id=session_id,
        name=file.filename or validation.filename or "dataset",
        version="original",
        original_filename=file.filename or validation.filename,
        file_type=validation.format or "csv",
        stored_filename=stored_filename,
        file_path=file_path,
        file_format=validation.format,
        file_size_bytes=validation.size_bytes,
        row_count=validation.row_count,
        column_count=validation.column_count,
        schema_info=schema_info,
    )

    db.add(dataset)
    session.status = "active"
    session.current_stage = "PROFILING"
    await db.commit()
    await db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        session_id=dataset.session_id,
        version=dataset.version,
        original_filename=dataset.original_filename,
        file_format=dataset.file_format,
        file_size_bytes=dataset.file_size_bytes,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        schema_info=dataset.schema_info,
        created_at=dataset.created_at.isoformat() if dataset.created_at else "",
    )


@router.get(
    "/{session_id}/datasets",
    response_model=List[DatasetResponse],
    summary="List all dataset versions for a session",
)
async def list_datasets(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns all versions (original, analysis, preprocessed, etc.) of datasets."""
    # Verify session
    session_query = await db.execute(select(Session).where(Session.id == session_id))
    if not session_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    query = await db.execute(
        select(Dataset)
        .where(Dataset.session_id == session_id)
        .order_by(Dataset.created_at.desc())
    )
    datasets = query.scalars().all()

    return [
        DatasetResponse(
            id=d.id,
            session_id=d.session_id,
            version=d.version,
            original_filename=d.original_filename,
            file_format=d.file_format,
            file_size_bytes=d.file_size_bytes,
            row_count=d.row_count,
            column_count=d.column_count,
            schema_info=d.schema_info,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in datasets
    ]


@router.get(
    "/{session_id}/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get metadata for a specific dataset version",
)
async def get_dataset(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found in session '{session_id}'.",
        )

    return DatasetResponse(
        id=dataset.id,
        session_id=dataset.session_id,
        version=dataset.version,
        original_filename=dataset.original_filename,
        file_format=dataset.file_format,
        file_size_bytes=dataset.file_size_bytes,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        schema_info=dataset.schema_info,
        created_at=dataset.created_at.isoformat() if dataset.created_at else "",
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    summary="Preview dataset records with pagination and column types",
)
async def preview_dataset(
    session_id: str,
    dataset_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    try:
        preview = storage_manager.get_dataset_preview(
            file_path=dataset.file_path,
            file_format=dataset.file_format,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load dataset preview: {str(exc)}",
        )

    return DatasetPreviewResponse(
        dataset_id=dataset.id,
        total_rows=preview["total_rows"],
        total_columns=preview["total_columns"],
        limit=limit,
        offset=offset,
        columns=[ColumnSummary(**c) for c in preview["columns"]],
        rows=preview["rows"],
    )


@router.get(
    "/{session_id}/datasets/{dataset_id}/download",
    summary="Download dataset file",
)
async def download_dataset(
    session_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = await db.execute(
        select(Dataset).where(Dataset.id == dataset_id, Dataset.session_id == session_id)
    )
    dataset = query.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    if not os.path.exists(dataset.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found on disk.",
        )

    return FileResponse(
        path=dataset.file_path,
        filename=dataset.original_filename,
        media_type="application/octet-stream",
    )
