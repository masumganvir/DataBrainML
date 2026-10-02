"""
DataWise AI — Fallback & Recovery System
Provides comprehensive reliability, confidentiality, error handling,
bounded retries, and independent post-recovery validation.
"""

from recovery.policies import (
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    RecoveryDecisionState,
    CircuitBreakerState,
    MAX_RETRIES,
    MAX_RECOVERY_ATTEMPTS,
    MAX_SAME_ERROR_ATTEMPTS,
    MAX_RECOVERY_TIME_SECONDS,
    MAX_COST_BUDGET,
)
from recovery.secret_redactor import SecretRedactor, detect_secrets, redact_secrets
from recovery.pii_redactor import PIIRedactor, detect_pii, redact_pii
from recovery.context_sanitizer import OutputSecurityGate
from recovery.safe_error_formatter import SafeErrorFormatter
from recovery.error_detector import ErrorDetector, ErrorObject
from recovery.error_classifier import ErrorClassifier
from recovery.root_cause_analyzer import RootCauseAnalyzer, RootCauseReport
from recovery.recovery_planner import RecoveryPlanner, RecoveryPlan
from recovery.retry_manager import RetryManager, CircuitBreaker
from recovery.fallback_router import FallbackRouter
from recovery.validation_manager import ValidationManager, ValidationReport
from recovery.rollback_manager import RollbackManager, CheckpointSnapshot
from recovery.escalation_manager import EscalationManager, EscalationRequest
from recovery.incident_manager import IncidentManager, RecoveryAuditRecord, SecurityIncidentRecord
from recovery.recovery_memory import RecoveryMemory, RecoveryPattern
from recovery.recovery_executor import RecoveryExecutor
from recovery.recovery_supervisor import FallbackRecoverySupervisor, SupervisorRecoveryResult

__all__ = [
    "ErrorCategory",
    "ErrorCode",
    "ErrorSeverity",
    "RecoveryDecisionState",
    "CircuitBreakerState",
    "MAX_RETRIES",
    "MAX_RECOVERY_ATTEMPTS",
    "MAX_SAME_ERROR_ATTEMPTS",
    "MAX_RECOVERY_TIME_SECONDS",
    "MAX_COST_BUDGET",
    "SecretRedactor",
    "detect_secrets",
    "redact_secrets",
    "PIIRedactor",
    "detect_pii",
    "redact_pii",
    "OutputSecurityGate",
    "SafeErrorFormatter",
    "ErrorDetector",
    "ErrorObject",
    "ErrorClassifier",
    "RootCauseAnalyzer",
    "RootCauseReport",
    "RecoveryPlanner",
    "RecoveryPlan",
    "RetryManager",
    "CircuitBreaker",
    "FallbackRouter",
    "ValidationManager",
    "ValidationReport",
    "RollbackManager",
    "CheckpointSnapshot",
    "EscalationManager",
    "EscalationRequest",
    "IncidentManager",
    "RecoveryAuditRecord",
    "SecurityIncidentRecord",
    "RecoveryMemory",
    "RecoveryPattern",
    "RecoveryExecutor",
    "FallbackRecoverySupervisor",
    "SupervisorRecoveryResult",
]
