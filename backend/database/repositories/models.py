"""
DataWise AI — Model Registry Repository
Implements Prompt Section 22, 23, 24, 25:
- Manages models and immutable model_versions
- Maintains lineage (v1 -> v2 -> v3) via parent_version_id
- Manages production pointer and safe zero-downtime rollback
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import ModelEntity, ModelVersion, Project


class ModelRepository:
    """Manages models, versions, metadata, and production promotion."""

    @classmethod
    async def register_model(
        cls,
        db: AsyncSession,
        project_id: str,
        name: str,
        task_type: str = "classification",
        description: str = "",
    ) -> ModelEntity:
        """Registers a logical model entity."""
        model = ModelEntity(
            id=f"mod_{uuid.uuid4().hex[:10]}",
            project_id=project_id,
            name=name,
            task_type=task_type,
            status="active",
        )
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model

    @classmethod
    async def create_version(
        cls,
        db: AsyncSession,
        model_id: str,
        version: str,
        algorithm: str,
        artifact_path: str,
        metrics: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        feature_names: List[str],
        parent_version_id: Optional[str] = None,
        is_production: bool = False,
    ) -> ModelVersion:
        """Creates an immutable model version with lineage tracking."""
        mv = ModelVersion(
            id=f"mv_{uuid.uuid4().hex[:10]}",
            model_id=model_id,
            version=version,
            algorithm=algorithm,
            artifact_path=artifact_path,
            metrics=metrics,
            hyperparameters=hyperparameters,
            feature_names=feature_names,
            parent_version_id=parent_version_id,
            is_champion=is_production,
            status="production" if is_production else "candidate",
        )
        db.add(mv)
        await db.commit()
        await db.refresh(mv)
        logger.info(f"[ModelRepository] Created {model_id} version {version} ({algorithm})")
        return mv

    @classmethod
    async def promote_to_production(
        cls,
        db: AsyncSession,
        model_id: str,
        version_id: str,
    ) -> None:
        """Safely promotes a version to production, unsetting previous champion."""
        # Unset previous
        await db.execute(
            update(ModelVersion)
            .where(ModelVersion.model_id == model_id)
            .values(is_champion=False, status="archived")
        )
        # Promote target
        await db.execute(
            update(ModelVersion)
            .where(ModelVersion.id == version_id)
            .values(is_champion=True, status="production")
        )
        await db.commit()
        logger.info(f"[ModelRepository] Promoted version {version_id} to production for model {model_id}")

    @classmethod
    async def rollback_to_version(
        cls,
        db: AsyncSession,
        model_id: str,
        target_version_id: str,
    ) -> bool:
        """Rolls back production pointer to a previously tested version."""
        stmt = select(ModelVersion).where(
            ModelVersion.model_id == model_id,
            ModelVersion.id == target_version_id,
        )
        res = await db.execute(stmt)
        target = res.scalar_one_or_none()
        if not target:
            return False

        await cls.promote_to_production(db, model_id, target_version_id)
        return True
