"""DataWise AI — Redis-Backed Distributed Job Queue

Enqueues asynchronous ML and data engineering tasks:
  - Profiling & Quality Analysis
  - Training & Optuna Tuning
  - Explainability (SHAP)
  - Report & Notebook Compilation
  - Retraining & Drift Audits
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Optional
from loguru import logger
from sqlalchemy import select, update

from app.cache.redis_client import get_redis_manager
from app.db.models.entities import BackgroundJob
from app.db.session import AsyncSessionLocal


class JobQueue:
    """Manages Redis-backed task dispatch with PostgreSQL persistence."""

    def __init__(self):
        self._redis_mgr = get_redis_manager()

    async def enqueue_job(
        self,
        job_type: str,
        payload: dict,
        project_id: Optional[str] = None,
        priority: int = 5,
        queue: str = "default",
    ) -> str:
        """Create job in PostgreSQL and enqueue into Redis priority list."""
        job_id = str(uuid.uuid4())

        # 1. Persist initial state in PostgreSQL
        async with AsyncSessionLocal() as session:
            job_record = BackgroundJob(
                id=job_id,
                project_id=project_id,
                job_type=job_type,
                status="pending",
                priority=priority,
                queue=queue,
                payload=payload,
                attempts=0,
                max_attempts=3,
                created_at=datetime.utcnow(),
            )
            session.add(job_record)
            await session.commit()

        # 2. Push job to Redis queue
        client = await self._redis_mgr.get_client()
        queue_key = f"queue:{queue}"
        job_envelope = {
            "id": job_id,
            "job_type": job_type,
            "project_id": project_id,
            "priority": priority,
            "payload": payload,
            "enqueued_at": datetime.utcnow().isoformat(),
        }

        try:
            if hasattr(client, "rpush"):
                await client.rpush(queue_key, json.dumps(job_envelope))
            # Cache status for instant polling
            await client.set(f"job:status:{job_id}", json.dumps({
                "id": job_id,
                "status": "pending",
                "job_type": job_type,
                "progress": 0,
            }), ex=86400)
        except Exception as e:
            logger.warning(f"Could not push to Redis queue: {e}")

        logger.info(f"Enqueued job {job_id} of type '{job_type}' to queue '{queue}'")
        return job_id

    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Fetch real-time job status from Redis or PostgreSQL."""
        client = await self._redis_mgr.get_client()
        cached = await client.get(f"job:status:{job_id}")
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass

        # Query PostgreSQL
        async with AsyncSessionLocal() as session:
            stmt = select(BackgroundJob).where(BackgroundJob.id == job_id)
            result = await session.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                return {
                    "id": job.id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "result": job.result,
                    "error": job.error,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                }
        return None

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[dict] = None,
        progress: int = 100,
    ) -> None:
        """Update job status in PostgreSQL and Redis."""
        now = datetime.utcnow()

        # Update Redis
        client = await self._redis_mgr.get_client()
        status_payload = {
            "id": job_id,
            "status": status,
            "progress": progress,
            "result": result,
            "error": error,
            "updated_at": now.isoformat(),
        }
        await client.set(f"job:status:{job_id}", json.dumps(status_payload), ex=86400)

        # Update PostgreSQL
        async with AsyncSessionLocal() as session:
            stmt = (
                update(BackgroundJob)
                .where(BackgroundJob.id == job_id)
                .values(
                    status=status,
                    result=result,
                    error=error,
                    completed_at=now if status in ("completed", "failed") else None,
                )
            )
            await session.execute(stmt)
            await session.commit()


_job_queue_singleton: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    global _job_queue_singleton
    if _job_queue_singleton is None:
        _job_queue_singleton = JobQueue()
    return _job_queue_singleton
