"""
DataWise AI — Agent Tool Permissions & Execution Modes

Defines:
  1. Fine-grained tool permissions
  2. Guided Mode (default) vs Autonomous Mode
  3. Immutable Decision Log & Safeguards
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from loguru import logger


class ToolPermission(str, Enum):
    READ_DATA = "READ_DATA"
    ANALYZE_DATA = "ANALYZE_DATA"
    GENERATE_PLOT = "GENERATE_PLOT"
    MODIFY_DATA = "MODIFY_DATA"
    TRAIN_MODEL = "TRAIN_MODEL"
    SAVE_MODEL = "SAVE_MODEL"
    GENERATE_NOTEBOOK = "GENERATE_NOTEBOOK"
    GENERATE_REPORT = "GENERATE_REPORT"

    # Potentially destructive operations
    REMOVE_ROWS = "REMOVE_ROWS"
    DROP_COLUMNS = "DROP_COLUMNS"
    REMOVE_OUTLIERS = "REMOVE_OUTLIERS"


DESTRUCTIVE_PERMISSIONS = {
    ToolPermission.REMOVE_ROWS,
    ToolPermission.DROP_COLUMNS,
    ToolPermission.REMOVE_OUTLIERS,
}


class DecisionLogEntry:
    def __init__(
        self,
        decision_key: str,
        target_entity: str,
        action: str,
        reason: str,
        confidence: Literal["HIGH", "MEDIUM", "LOW", "NEEDS_HUMAN_REVIEW"],
        user_approved: bool,
        mode: Literal["guided", "autonomous"],
    ):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.decision_key = decision_key
        self.target_entity = target_entity
        self.action = action
        self.reason = reason
        self.confidence = confidence
        self.user_approved = user_approved
        self.mode = mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "decision_key": self.decision_key,
            "target_entity": self.target_entity,
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
            "user_approved": self.user_approved,
            "mode": self.mode,
        }


class PermissionManager:
    """
    Enforces permission gates between Guided and Autonomous execution modes.
    """

    @staticmethod
    def is_action_allowed(
        permission: ToolPermission,
        mode: Literal["guided", "autonomous"] = "guided",
        user_approved: bool = False,
        is_target_signal: bool = False,
    ) -> Tuple[bool, str]:
        """
        Validates whether an agent action is permissible.
        In Guided mode, all destructive operations require explicit human approval.
        In Autonomous mode, standard preprocessing proceeds automatically, but safeguards
        strictly forbid deleting target-related observations or dropping unverified columns.
        """
        if permission not in DESTRUCTIVE_PERMISSIONS:
            return True, f"Permission {permission.value} granted."

        # Guard 1: Never delete potential target signal (e.g. fraud outliers)
        if is_target_signal and permission in [ToolPermission.REMOVE_OUTLIERS, ToolPermission.REMOVE_ROWS]:
            return False, "FORBIDDEN: Safeguard prevented deletion of observations carrying valuable target/anomaly signal."

        # Guard 2: Guided Mode requires human confirmation
        if mode == "guided":
            if user_approved:
                return True, f"Destructive operation {permission.value} approved by user."
            return False, f"HUMAN_APPROVAL_REQUIRED: Destructive operation '{permission.value}' requires explicit user confirmation in Guided Mode."

        # Guard 3: Autonomous Mode safeguards
        if mode == "autonomous":
            if permission == ToolPermission.DROP_COLUMNS and not user_approved:
                # Column drops must still require consensus even in autonomous mode
                return False, "HUMAN_APPROVAL_REQUIRED: Dropping columns irreversibly removes dimensionality; user confirmation required."
            return True, f"Operation {permission.value} authorized under Autonomous Mode safety constraints."

        return False, "Unauthorized execution mode."
