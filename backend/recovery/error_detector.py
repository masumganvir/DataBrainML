"""
Error Detector
Monitors exceptions, return codes, schemas, timeouts, and state failures,
converting raw diagnostics into structured, secret-sanitized ErrorObjects.
"""

from __future__ import annotations

import hashlib
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field

from recovery.policies import (
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    RETRYABLE_CATEGORIES,
    SECURITY_HALT_CATEGORIES,
)
from recovery.secret_redactor import SecretRedactor
from recovery.pii_redactor import PIIRedactor
from recovery.context_sanitizer import OutputSecurityGate


class ErrorObject(BaseModel):
    """Structured internal error contract."""
    error_id: str = Field(default_factory=lambda: f"ERR-{uuid.uuid4().hex[:8].upper()}")
    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    workflow_id: str = Field(default="default_workflow")
    agent_id: str = Field(default="unknown_agent")
    node_id: str = Field(default="unknown_node")
    category: ErrorCategory = Field(default=ErrorCategory.UNKNOWN)
    severity: ErrorSeverity = Field(default=ErrorSeverity.RECOVERABLE)
    error_code: ErrorCode = Field(default=ErrorCode.ERR_UNKNOWN)
    stage: str = Field(default="general")
    retryable: bool = Field(default=False)
    recoverable: bool = Field(default=True)
    user_safe: bool = Field(default=True)
    message: str = Field(default="")
    safe_message: str = Field(default="")
    recommended_action: str = Field(default="")
    attempt_count: int = Field(default=1)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    secret_detected: bool = Field(default=False)
    stack_trace_hash: Optional[str] = Field(default=None)
    raw_exception_name: Optional[str] = Field(default=None)
    context_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class ErrorDetector:
    """Detects and captures unstructured errors, normalizing them into sanitized ErrorObjects."""

    @classmethod
    def detect_and_normalize(
        cls,
        exception: Optional[Union[Exception, str]] = None,
        stage: str = "execution",
        agent_id: str = "unknown_agent",
        node_id: str = "unknown_node",
        workflow_id: str = "default_workflow",
        attempt_count: int = 1,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorObject:
        """Converts raw exception or error message into a structured ErrorObject."""
        ctx = context or {}
        raw_msg = str(exception) if exception else "An unknown operation error occurred."
        exc_type = type(exception).__name__ if isinstance(exception, Exception) else "RuntimeError"

        # Check for secrets before storing anything
        has_secret = SecretRedactor.detect_secrets(raw_msg) or SecretRedactor.detect_secrets(str(ctx))
        sanitized_msg = SecretRedactor.redact_secrets(raw_msg)
        sanitized_msg = PIIRedactor.redact_pii(sanitized_msg)

        # Hash stack trace for secure correlation without leaking paths
        stack_hash = None
        if isinstance(exception, Exception):
            try:
                tb_str = traceback.format_exc()
                if tb_str and "NoneType: None" not in tb_str:
                    stack_hash = hashlib.sha256(tb_str.encode("utf-8")).hexdigest()[:16]
            except Exception:
                pass

        # Safe sanitized metadata
        clean_context = OutputSecurityGate.sanitize(ctx)

        # Initial baseline object (Classification will refine category & code)
        return ErrorObject(
            workflow_id=workflow_id,
            agent_id=agent_id,
            node_id=node_id,
            stage=stage,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.RECOVERABLE,
            error_code=ErrorCode.ERR_UNKNOWN,
            retryable=False,
            recoverable=True,
            user_safe=True,
            message=sanitized_msg,
            safe_message=sanitized_msg,
            recommended_action="Inspect stage logs or retry with valid input.",
            attempt_count=attempt_count,
            secret_detected=has_secret,
            stack_trace_hash=stack_hash,
            raw_exception_name=exc_type,
            context_metadata=clean_context,
        )
