"""
Escalation Manager
Handles security stops, human-in-the-loop approval workflows, and unrecoverable alerts.
Enforces that destructive operations (e.g. column drops, target changes, model overwrites)
never proceed automatically without explicit user authorization.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from recovery.policies import RecoveryDecisionState


class EscalationRequest(BaseModel):
    escalation_id: str = Field(default_factory=lambda: f"ESC-{uuid.uuid4().hex[:8].upper()}")
    workflow_id: str
    error_id: str
    reason: str
    action_type: str
    requires_approval: bool = True
    approved: Optional[bool] = None
    approval_options: List[str] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False


class EscalationManager:
    """Coordinates manual approvals, safety freezes, and administrative escalations."""

    DESTRUCTIVE_ACTIONS = {
        "change_target",
        "drop_columns",
        "remove_significant_records",
        "change_production_model",
        "alter_database_write_permissions",
        "overwrite_production_model",
        "destructive_db_operation",
    }

    def __init__(self):
        self._pending_escalations: Dict[str, EscalationRequest] = {}
        self._resolved_escalations: Dict[str, EscalationRequest] = {}

    def is_destructive_action(self, action_name: str) -> bool:
        return action_name.lower().strip() in self.DESTRUCTIVE_ACTIONS

    def create_escalation(
        self,
        workflow_id: str,
        error_id: str,
        reason: str,
        action_type: str,
        approval_options: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationRequest:
        """Issues an escalation request, pausing the affected workflow until resolved."""
        req = EscalationRequest(
            workflow_id=workflow_id,
            error_id=error_id,
            reason=reason,
            action_type=action_type,
            requires_approval=True,
            approval_options=approval_options or ["Approve", "Reject", "Abort"],
            context_data=context or {},
        )
        self._pending_escalations[req.escalation_id] = req
        logger.warning(
            f"Escalation {req.escalation_id} created for workflow {workflow_id} (Reason: {reason})"
        )
        return req

    def resolve_escalation(
        self, escalation_id: str, approved: bool, user_comment: str = ""
    ) -> Optional[EscalationRequest]:
        """Resolves an escalation when human operator provides authorization."""
        req = self._pending_escalations.pop(escalation_id, None)
        if not req:
            return None

        req.approved = approved
        req.resolved = True
        req.context_data["user_comment"] = user_comment
        self._resolved_escalations[escalation_id] = req
        logger.info(
            f"Escalation {escalation_id} resolved: approved={approved} ({user_comment})"
        )
        return req

    def get_pending(self, workflow_id: Optional[str] = None) -> List[EscalationRequest]:
        if workflow_id:
            return [
                req for req in self._pending_escalations.values() if req.workflow_id == workflow_id
            ]
        return list(self._pending_escalations.values())
