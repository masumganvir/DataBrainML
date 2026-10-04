"""
DataWise AI — Artifact Repository
Tracks all generated artifacts (.ipynb, .pkl, .html, .pdf, .png, .zip),
ensuring checksum integrity and secure tenant-isolated retrieval.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import ArtifactEntity, Project


class ArtifactRepository:
    """Manages artifact metadata, storage pointers, and download authorization."""

    @classmethod
    async def register_artifact(
        cls,
        db: AsyncSession,
        project_id: str,
        run_id: str,
        artifact_type: str,
        filename: str,
        storage_key: str,
        size_bytes: int,
        sha256: str,
        mime_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactEntity:
        """Registers a newly generated artifact in the database."""
        artifact = ArtifactEntity(
            id=f"art_{uuid.uuid4().hex[:10]}",
            project_id=project_id,
            run_id=run_id,
            artifact_type=artifact_type,
            name=filename,
            file_path=storage_key,
            file_size_bytes=size_bytes,
            mime_type=mime_type,
            sha256_hash=sha256,
            metadata_info=metadata or {},
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        logger.info(f"[ArtifactRepository] Registered {artifact_type} ({filename}) for project {project_id}")
        return artifact

    @classmethod
    async def get_artifact_by_id(
        cls,
        db: AsyncSession,
        artifact_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> Optional[ArtifactEntity]:
        """
        Retrieves artifact ensuring user ownership via Project join.
        Guarantees that a user can never download another user's artifacts.
        """
        stmt = (
            select(ArtifactEntity)
            .join(Project, Project.id == ArtifactEntity.project_id)
            .where(ArtifactEntity.id == artifact_id)
        )
        if not is_admin:
            stmt = stmt.where(Project.user_id == owner_id)

        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_project_artifacts(
        cls,
        db: AsyncSession,
        project_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> List[ArtifactEntity]:
        """Lists all artifacts for a project with owner verification."""
        stmt = (
            select(ArtifactEntity)
            .join(Project, Project.id == ArtifactEntity.project_id)
            .where(ArtifactEntity.project_id == project_id)
        )
        if not is_admin:
            stmt = stmt.where(Project.user_id == owner_id)

        res = await db.execute(stmt)
        return list(res.scalars().all())
