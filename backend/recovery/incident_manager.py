"""
Incident Manager & Audit Trail
Records every recovery event, security violation, and diagnosis into an immutable,
secret-sanitized audit log.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from recovery.context_sanitizer import OutputSecurityGate
from recovery.policies import RecoveryDecisionState


class RecoveryAuditRecord(BaseModel):
    audit_id: str = Field(default_factory=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    workflow_id: str
    error_id: str
    stage: str
    diagnosis: str
    decision: RecoveryDecisionState
    action_taken: str
    validation_status: str
    execution_time_seconds: float
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityIncidentRecord(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"SEC-{uuid.uuid4().hex[:8].upper()}")
    workflow_id: str
    error_id: str
    threat_type: str
    timestamp: float = Field(default_factory=time.time)
    details: Dict[str, Any] = Field(default_factory=dict)


class IncidentManager:
    """Manages secure auditing and security incident records."""

    def __init__(self):
        self._audit_records: List[RecoveryAuditRecord] = []
        self._security_incidents: List[SecurityIncidentRecord] = []

    def log_recovery_audit(
        self,
        workflow_id: str,
        error_id: str,
        stage: str,
        diagnosis: str,
        decision: RecoveryDecisionState,
        action_taken: str,
        validation_status: str,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryAuditRecord:
        """Appends sanitized recovery audit log."""
        safe_diag = OutputSecurityGate.sanitize_text(diagnosis)
        safe_action = OutputSecurityGate.sanitize_text(action_taken)
        clean_meta = OutputSecurityGate.sanitize(metadata or {})

        record = RecoveryAuditRecord(
            workflow_id=workflow_id,
            error_id=error_id,
            stage=stage,
            diagnosis=safe_diag,
            decision=decision,
            action_taken=safe_action,
            validation_status=validation_status,
            execution_time_seconds=round(execution_time, 4),
            metadata=clean_meta,
        )
        self._audit_records.append(record)
        logger.info(
            f"Recovery Audit [{record.audit_id}] workflow={workflow_id} decision={decision.value} result={validation_status}"
        )
        return record

    def log_security_incident(
        self,
        workflow_id: str,
        error_id: str,
        threat_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityIncidentRecord:
        """Records security incident without retaining confidential token contents."""
        clean_details = OutputSecurityGate.sanitize(details or {})
        rec = SecurityIncidentRecord(
            workflow_id=workflow_id,
            error_id=error_id,
            threat_type=threat_type,
            details=clean_details,
        )
        self._security_incidents.append(rec)
        logger.critical(
            f"SECURITY INCIDENT [{rec.incident_id}] workflow={workflow_id} threat={threat_type}"
        )
        return rec

    def get_audit_trail(self, workflow_id: Optional[str] = None) -> List[RecoveryAuditRecord]:
        if workflow_id:
            return [r for r in self._audit_records if r.workflow_id == workflow_id]
        return list(self._audit_records)

    def get_security_incidents(self) -> List[SecurityIncidentRecord]:
        return list(self._security_incidents)
