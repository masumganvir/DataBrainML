"""DataWise AI — Append-Only Security & Operational Audit Logger

Records immutable audit entries for critical system operations:
  - User authentications (login, logout)
  - Dataset lifecycle (upload, versioning, deletion)
  - Experiments & Model Training
  - Model Promotions & Deployments
  - API Key creations & revocations
  - RBAC policy changes
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Optional
from loguru import logger
from starlette.requests import Request

from app.db.models.entities import AuditLog
from app.db.session import AsyncSessionLocal


class AuditLogger:
    """Async logger for recording append-only audit entries."""

    @staticmethod
    def _hash_ip(ip: Optional[str]) -> Optional[str]:
        if not ip:
            return None
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

    @classmethod
    async def log(
        cls,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        request: Optional[Request] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Create and commit an immutable audit record."""
        audit_id = str(uuid.uuid4())
        ip_hash = None
        user_agent = None

        if request:
            client_ip = request.client.host if request.client else None
            ip_hash = cls._hash_ip(client_ip)
            user_agent = request.headers.get("User-Agent")

        try:
            async with AsyncSessionLocal() as session:
                record = AuditLog(
                    id=audit_id,
                    user_id=user_id,
                    project_id=project_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_hash=ip_hash,
                    user_agent=user_agent[:255] if user_agent else None,
                    audit_metadata=metadata,
                    created_at=datetime.utcnow(),
                )
                session.add(record)
                await session.commit()
            return audit_id
        except Exception as e:
            logger.error(f"Failed to record audit log for action '{action}': {e}")
            return audit_id
