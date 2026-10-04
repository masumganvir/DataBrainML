"""
DataWise AI — Dataset Repository
Manages dataset metadata, cryptographic SHA-256 fingerprinting,
and historical dataset versions without storing heavy raw payloads in the database.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import DatasetEntity, DatasetVersion, Project


class DatasetRepository:
    """Handles dataset metadata and lineage tracking."""

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        project_id: str,
        name: str,
        original_filename: str,
        file_size: int,
        sha256: str,
        storage_key: str,
        file_type: str = "csv",
        row_count: int = 0,
        column_count: int = 0,
        schema: Optional[Dict[str, Any]] = None,
        target_column: Optional[str] = None,
    ) -> DatasetEntity:
        """Registers uploaded dataset metadata."""
        dataset_id = f"ds_{uuid.uuid4().hex[:10]}"
        ds = DatasetEntity(
            id=dataset_id,
            project_id=project_id,
            name=name,
            original_filename=original_filename,
            file_size=file_size,
            file_type=file_type,
            sha256=sha256,
            storage_path=storage_key,
            row_count=row_count,
            column_count=column_count,
            schema_metadata=schema or {},
            target_column=target_column,
            is_active=True,
        )
        db.add(ds)

        # Create Version 1 in dataset_versions lineage
        v1 = DatasetVersion(
            id=f"dsv_{uuid.uuid4().hex[:10]}",
            dataset_id=dataset_id,
            version_number=1,
            row_count=row_count,
            column_count=column_count,
            file_size=file_size,
            sha256_hash=sha256,
            storage_path=storage_key,
            description="Initial uploaded version",
        )
        db.add(v1)

        await db.commit()
        await db.refresh(ds)
        return ds

    @classmethod
    async def find_duplicate_by_hash(
        cls,
        db: AsyncSession,
        project_id: str,
        sha256: str,
    ) -> Optional[DatasetEntity]:
        """Checks if identical dataset hash already exists under this project."""
        stmt = select(DatasetEntity).where(
            DatasetEntity.project_id == project_id,
            DatasetEntity.sha256 == sha256,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_versions(
        cls,
        db: AsyncSession,
        dataset_id: str,
    ) -> List[DatasetVersion]:
        """Returns version history of a dataset (v1, v2, v3)."""
        stmt = select(DatasetVersion).where(
            DatasetVersion.dataset_id == dataset_id
        ).order_by(DatasetVersion.version_number.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
