"""
Recovery Supervisor
Central FallbackRecoverySupervisor coordinating error detection, classification,
root cause analysis, bounded recovery execution, independent validation,
checkpoint rollbacks, and confidential user reporting.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Union
from loguru import logger
from pydantic import BaseModel, Field

from recovery.context_sanitizer import OutputSecurityGate
from recovery.error_classifier import ErrorClassifier
from recovery.error_detector import ErrorDetector, ErrorObject
from recovery.escalation_manager import EscalationManager
from recovery.fallback_router import FallbackRouter
from recovery.incident_manager import IncidentManager
from recovery.policies import RecoveryDecisionState
from recovery.recovery_executor import RecoveryExecutor
from recovery.recovery_memory import RecoveryMemory
from recovery.recovery_planner import RecoveryPlanner
from recovery.retry_manager import RetryManager
from recovery.rollback_manager import RollbackManager
from recovery.safe_error_formatter import SafeErrorFormatter
from recovery.validation_manager import ValidationReport


class SupervisorRecoveryResult(BaseModel):
    success: bool
    decision: RecoveryDecisionState
    error_id: str
    stage: str
    safe_message: str
    user_panel: str
    api_response: Dict[str, Any]
    recovered_state: Optional[Dict[str, Any]] = None
    validation_report: Optional[ValidationReport] = None
    checkpoint_resumed: Optional[str] = None
    retry_delay_seconds: float = 0.0

    class Config:
        arbitrary_types_allowed = True


class FallbackRecoverySupervisor:
    """Master supervisor governing automated recovery, confidentiality, and system stability."""

    def __init__(self):
        self.error_detector = ErrorDetector()
        self.error_classifier = ErrorClassifier()
        self.root_cause_analyzer = None  # Loaded on demand or classmethods
        self.retry_manager = RetryManager()
        self.fallback_router = FallbackRouter()
        self.rollback_manager = RollbackManager()
        self.escalation_manager = EscalationManager()
        self.incident_manager = IncidentManager()
        self.recovery_memory = RecoveryMemory()

    def handle_failure(
        self,
        exception: Union[Exception, str],
        stage: str = "execution",
        agent_id: str = "unknown_agent",
        node_id: str = "unknown_node",
        workflow_id: str = "default_workflow",
        attempt_count: int = 1,
        system_state: Optional[Dict[str, Any]] = None,
    ) -> SupervisorRecoveryResult:
        """
        Coordinates full failure resolution cycle:
        Detect -> Classify -> Root Cause -> Plan -> Bound Check -> Execute -> Validate -> Resume/Escalate.
        """
        t0 = time.time()
        state = system_state or {}

        # 1. Error Detection & Normalization (Sanitizes raw secrets)
        error_obj: ErrorObject = self.error_detector.detect_and_normalize(
            exception=exception,
            stage=stage,
            agent_id=agent_id,
            node_id=node_id,
            workflow_id=workflow_id,
            attempt_count=attempt_count,
            context=state,
        )

        # 2. Error Classification
        error_obj = self.error_classifier.classify(error_obj)

        # 3. Security Stop Check
        if error_obj.secret_detected or error_obj.category.value == "SECURITY":
            self.incident_manager.log_security_incident(
                workflow_id=workflow_id,
                error_id=error_obj.error_id,
                threat_type="CREDENTIAL_OR_SECURITY_POLICY_VIOLATION",
                details={"stage": stage, "agent": agent_id},
            )
            api_resp = SafeErrorFormatter.format_security_incident_response(error_obj.error_id)
            user_panel = SafeErrorFormatter.format_user_panel(
                error_id=error_obj.error_id,
                status=RecoveryDecisionState.SECURITY_STOP,
                stage=stage,
                what_happened="Processing halted by security boundary.",
                reason="A security-sensitive operation or confidential token was detected.",
                recovery_attempted="Operation was blocked immediately to protect credentials.",
                recovery_result="Security halt enforced.",
                recommended_action="Verify permissions and remove sensitive credentials from input.",
                reference_id=error_obj.error_id,
            )
            return SupervisorRecoveryResult(
                success=False,
                decision=RecoveryDecisionState.SECURITY_STOP,
                error_id=error_obj.error_id,
                stage=stage,
                safe_message=error_obj.safe_message,
                user_panel=user_panel,
                api_response=api_resp,
            )

        # 4. Root Cause Analysis
        from recovery.root_cause_analyzer import RootCauseAnalyzer
        root_cause = RootCauseAnalyzer.analyze(error_obj, state)

        # 5. Recovery Planning
        plan = RecoveryPlanner.plan(error_obj, root_cause)

        # 6. Retry & Loop Safety Check
        is_allowed, decision_state, bound_reason = self.retry_manager.evaluate_retry_eligibility(
            workflow_id=workflow_id,
            agent_id=agent_id,
            error_signature=error_obj.message[:40],
            strategy_name=plan.strategy_name,
            attempt_count=attempt_count,
        )

        if not is_allowed:
            # Checkpoint Rollback Attempt
            safe_checkpoint = self.rollback_manager.get_nearest_safe_checkpoint(workflow_id, stage)
            cp_id = safe_checkpoint.checkpoint_id if safe_checkpoint else None

            user_panel = SafeErrorFormatter.format_user_panel(
                error_id=error_obj.error_id,
                status=decision_state,
                stage=stage,
                what_happened=error_obj.safe_message or "Execution failed repeatedly.",
                reason=bound_reason,
                recovery_attempted=f"Attempted {attempt_count} recoveries using {plan.strategy_name}.",
                recovery_result=f"Halted under safety policy ({decision_state.value}).",
                recommended_action="Inspect parameters or resume from nearest checkpoint.",
                reference_id=error_obj.error_id,
            )
            api_resp = SafeErrorFormatter.format_api_response(
                error_id=error_obj.error_id,
                error_code=error_obj.error_code,
                message=error_obj.safe_message,
                hint=bound_reason,
                retryable=False,
                status=decision_state.value,
            )
            return SupervisorRecoveryResult(
                success=False,
                decision=decision_state,
                error_id=error_obj.error_id,
                stage=stage,
                safe_message=error_obj.safe_message,
                user_panel=user_panel,
                api_response=api_resp,
                checkpoint_resumed=cp_id,
            )

        # 7. Plan Execution & Validation Gate
        decision, updated_state, val_report = RecoveryExecutor.execute_plan(
            plan=plan,
            error_obj=error_obj,
            current_state=state,
        )

        elapsed = time.time() - t0

        # 8. Record Audit Trail & Memory
        self.incident_manager.log_recovery_audit(
            workflow_id=workflow_id,
            error_id=error_obj.error_id,
            stage=stage,
            diagnosis=root_cause.primary_cause,
            decision=decision,
            action_taken=plan.strategy_name,
            validation_status="PASSED" if val_report.is_valid else "FAILED",
            execution_time=elapsed,
        )

        if val_report.is_valid:
            self.recovery_memory.record_validated_pattern(
                error_signature=error_obj.message[:40],
                solution_strategy=plan.strategy_name,
                validation_standard=val_report.stage,
                is_successful=True,
            )

        # 9. Format Safe Output
        user_panel = SafeErrorFormatter.format_user_panel(
            error_id=error_obj.error_id,
            status=decision,
            stage=stage,
            what_happened=f"An issue occurred during {stage}.",
            reason=root_cause.primary_cause,
            recovery_attempted=plan.strategy_name,
            recovery_result="Validation passed successfully." if val_report.is_valid else "Recovery could not be validated safely.",
            recommended_action=error_obj.recommended_action,
            reference_id=error_obj.error_id,
        )
        api_resp = SafeErrorFormatter.format_api_response(
            error_id=error_obj.error_id,
            error_code=error_obj.error_code,
            message=error_obj.safe_message,
            hint=error_obj.recommended_action,
            retryable=decision == RecoveryDecisionState.RETRY_REQUIRED,
            status=decision.value,
        )

        delay = 0.0
        if decision == RecoveryDecisionState.RETRY_REQUIRED:
            delay = self.retry_manager.calculate_backoff(attempt_count)

        return SupervisorRecoveryResult(
            success=val_report.is_valid,
            decision=decision,
            error_id=error_obj.error_id,
            stage=stage,
            safe_message=error_obj.safe_message,
            user_panel=user_panel,
            api_response=api_resp,
            recovered_state=updated_state if val_report.is_valid else None,
            validation_report=val_report,
            retry_delay_seconds=delay,
        )
