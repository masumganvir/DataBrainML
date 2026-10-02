"""
DataWise AI — AuditAgent (Section 5 & 45)
Records immutable governance audit events, user approvals, model lineage,
PII detection alerts, and production lifecycle state transitions.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class AuditRecord(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    event_type: str  # "DATASET_UPLOAD", "TRAINING_COMPLETED", "APPROVAL_GRANTED", "MODEL_DEPLOYED", "ROLLBACK", "ALERT"
    actor_id: str
    project_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "INFO"  # "INFO", "WARNING", "CRITICAL"


class AuditAgent(BaseAgent):
    """Tracks and validates immutable audit records across platform operations."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="AuditAgent")
        self._audit_log: List[AuditRecord] = []

    def record_event(
        self,
        event_type: str,
        actor_id: str,
        project_id: str,
        details: Dict[str, Any],
        severity: str = "INFO",
    ) -> AuditRecord:
        rec = AuditRecord(
            event_type=event_type,
            actor_id=actor_id,
            project_id=project_id,
            details=details,
            severity=severity,
        )
        self._audit_log.append(rec)
        logger.info(f"[AuditAgent] [{severity}] {event_type} by {actor_id} on {project_id}")
        return rec

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        event_type = input_data.parameters.get("event_type", "GENERIC_EVENT")
        actor_id = input_data.parameters.get("actor_id", "system")
        project_id = input_data.parameters.get("project_id", input_data.session_id)
        details = input_data.parameters.get("details", {})
        severity = input_data.parameters.get("severity", "INFO")

        try:
            record = self.record_event(
                event_type=event_type,
                actor_id=actor_id,
                project_id=project_id,
                details=details,
                severity=severity,
            )
            return AgentOutput(
                success=True,
                data=record.model_dump(),
                message=f"Audit event {record.audit_id} registered successfully",
            )
        except Exception as e:
            logger.error(f"[AuditAgent] Error recording audit event: {e}")
            return AgentOutput(success=False, errors=[str(e)])
