"""
DataWise AI — Run & Experiment Repository
Tracks pipeline executions, agent execution sequences, timings, and outcomes.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import ExperimentRun, AgentRun, PipelineStage, Project


class RunRepository:
    """Manages experiment runs, agent execution history, and stage tracking."""

    @classmethod
    async def create_run(
        cls,
        db: AsyncSession,
        project_id: str,
        run_id: str,
        name: str = "Automated ML Run",
        config: Optional[Dict[str, Any]] = None,
    ) -> ExperimentRun:
        """Initializes a new pipeline run record."""
        run = ExperimentRun(
            id=run_id,
            project_id=project_id,
            run_number=1,
            name=name,
            status="running",
            run_metadata=config or {},
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

    @classmethod
    async def update_status(
        cls,
        db: AsyncSession,
        run_id: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Updates run status upon completion or failure."""
        from datetime import datetime
        stmt = (
            update(ExperimentRun)
            .where(ExperimentRun.id == run_id)
            .values(
                status=status,
                completed_at=datetime.utcnow() if status in ("completed", "failed") else None,
                metrics_summary=metrics or {},
            )
        )
        await db.execute(stmt)
        await db.commit()

    @classmethod
    async def log_agent_execution(
        cls,
        db: AsyncSession,
        run_id: str,
        agent_name: str,
        status: str = "completed",
        duration_ms: float = 0.0,
        summary: str = "",
    ) -> None:
        """Records granular agent execution log."""
        from datetime import datetime
        agent_run = AgentRun(
            id=f"ag_{uuid.uuid4().hex[:10]}",
            agent_name=agent_name,
            status=status,
            duration_ms=duration_ms,
            created_at=datetime.utcnow(),
        )
        db.add(agent_run)
        await db.commit()
