"""
DataWise AI — Project Repository
Enforces 100% User Isolation: All project queries require both project_id AND owner_id.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import Project


class ProjectRepository:
    """Manages project persistence with mandatory user ownership checks."""

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        owner_id: str,
        name: str = "New ML Project",
        description: str = "",
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """Creates a new project strictly bound to the authenticated owner_id."""
        project_id = f"proj_{uuid.uuid4().hex[:10]}"
        proj = Project(
            id=project_id,
            user_id=owner_id,
            name=name,
            description=description,
            status="active",
            configuration=configuration or {},
        )
        db.add(proj)
        await db.commit()
        await db.refresh(proj)
        logger.info(f"[ProjectRepository] Created project {proj.id} for owner {owner_id}")
        return proj

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        project_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> Optional[Project]:
        """
        Retrieves project with mandatory owner_id verification.
        Non-admins can NEVER view a project they do not own.
        """
        stmt = select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
        if not is_admin:
            stmt = stmt.where(Project.user_id == owner_id)
        
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def list_for_user(
        cls,
        db: AsyncSession,
        owner_id: str,
        is_admin: bool = False,
    ) -> List[Project]:
        """Lists only projects owned by the authenticated user."""
        stmt = select(Project).where(Project.deleted_at.is_(None)).order_by(Project.created_at.desc())
        if not is_admin:
            stmt = stmt.where(Project.user_id == owner_id)

        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        project_id: str,
        owner_id: str,
        updates: Dict[str, Any],
        is_admin: bool = False,
    ) -> Optional[Project]:
        """Updates project ensuring owner verification."""
        proj = await cls.get_by_id(db, project_id, owner_id, is_admin=is_admin)
        if not proj:
            return None

        for k, v in updates.items():
            if hasattr(proj, k) and k not in ("id", "user_id"):
                setattr(proj, k, v)

        await db.commit()
        await db.refresh(proj)
        return proj

    @classmethod
    async def soft_delete(
        cls,
        db: AsyncSession,
        project_id: str,
        owner_id: str,
        is_admin: bool = False,
    ) -> bool:
        """Soft-deletes project to allow audit recovery."""
        from datetime import datetime
        proj = await cls.get_by_id(db, project_id, owner_id, is_admin=is_admin)
        if not proj:
            return False

        proj.deleted_at = datetime.utcnow()
        proj.status = "archived"
        await db.commit()
        return True
