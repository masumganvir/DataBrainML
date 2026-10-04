"""
DataWise AI — Security & Audit Service
Implements Prompt Section 34, 57, 58:
- Audit trail for all security-sensitive actions:
    login, logout, project_created, dataset_uploaded, run_started,
    model_created, artifact_downloaded, model_promoted, model_rolled_back
- Never logs sensitive passwords, raw credentials, or PII rows
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import AuditLog


class SecurityService:
    """Manages audit logging and confidential data redaction."""

    @staticmethod
    def mask_sensitive_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Masks sensitive fields like passwords, tokens, and secret keys."""
        masked = {}
        sensitive_patterns = ("password", "secret", "token", "key", "api_key", "jwt")
        for k, v in payload.items():
            if any(p in k.lower() for p in sensitive_patterns):
                masked[k] = "******"
            elif isinstance(v, dict):
                masked[k] = SecurityService.mask_sensitive_dict(v)
            else:
                masked[k] = v
        return masked

    @classmethod
    async def record_audit_event(
        cls,
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Persists audit record in database."""
        safe_details = cls.mask_sensitive_dict(details or {})
        ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest() if ip_address else None
        audit = AuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_hash=ip_hash,
            audit_metadata=safe_details,
        )
        db.add(audit)
        await db.commit()
        logger.info(f"[Audit] User {user_id} performed '{action}' on {resource_type}:{resource_id}")
        return audit


security_service = SecurityService()
