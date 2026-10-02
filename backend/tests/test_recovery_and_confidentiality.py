"""
Test Suite: Fallback & Recovery Agent System & Confidentiality Layer
Verifies secret redaction, PII protection, bounded retries, loop prevention,
post-recovery validation gates, recovery agents, and the recovery graph.
"""

import json
import pytest
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from recovery.policies import (
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    RecoveryDecisionState,
    MAX_RETRIES,
    MAX_RECOVERY_ATTEMPTS,
    MAX_SAME_ERROR_ATTEMPTS,
)
from recovery.secret_redactor import SecretRedactor, detect_secrets, redact_secrets
from recovery.pii_redactor import PIIRedactor, detect_pii, redact_pii
from recovery.context_sanitizer import OutputSecurityGate
from recovery.safe_error_formatter import SafeErrorFormatter
from recovery.error_detector import ErrorDetector, ErrorObject
from recovery.error_classifier import ErrorClassifier
from recovery.root_cause_analyzer import RootCauseAnalyzer, RootCauseReport
from recovery.recovery_planner import RecoveryPlanner, RecoveryPlan
from recovery.recovery_executor import RecoveryExecutor
from recovery.retry_manager import RetryManager, CircuitBreaker
from recovery.fallback_router import FallbackRouter
from recovery.validation_manager import ValidationManager, ValidationReport
from recovery.rollback_manager import RollbackManager
from recovery.escalation_manager import EscalationManager
from recovery.incident_manager import IncidentManager
from recovery.recovery_memory import RecoveryMemory
from recovery.recovery_supervisor import FallbackRecoverySupervisor

from agents.base import AgentInput
from agents.recovery.fallback_supervisor_agent.agent import FallbackSupervisorAgent
from agents.recovery.error_detection_agent.agent import ErrorDetectionAgent
from agents.recovery.error_classification_agent.agent import ErrorClassificationAgent
from agents.recovery.root_cause_agent.agent import RootCauseAgent
from agents.recovery.recovery_planning_agent.agent import RecoveryPlanningAgent
from agents.recovery.recovery_execution_agent.agent import RecoveryExecutionAgent
from agents.recovery.retry_decision_agent.agent import RetryDecisionAgent
from agents.recovery.validation_agent.agent import ValidationAgent
from agents.recovery.rollback_agent.agent import RollbackAgent
from agents.recovery.escalation_agent.agent import EscalationAgent
from agents.recovery.confidentiality_agent.agent import ConfidentialityAgent
from agents.recovery.error_explanation_agent.agent import ErrorExplanationAgent

from graphs.recovery_graph import build_recovery_graph, RecoveryState


# =====================================================================
# 1. SECRET & CREDENTIAL REDACTION TESTS
# =====================================================================

def test_secret_redactor_masks_api_keys():
    gemini_key = "AQ.MOCK_TEST_KEY_FOR_REDACTION_TESTING_123456789"
    groq_key = "gsk_MOCK_TEST_KEY_FOR_REDACTION_TESTING_123456789"
    cf_key = "cf_mock_token_TEST_FOR_REDACTION_TESTING_123456789"
    openai_key = "sk-mock-test-key-for-redaction-testing-123456789"

    raw_text = f"Errors encountered with Gemini {gemini_key} and Groq {groq_key} and CF {cf_key} and {openai_key}"
    assert detect_secrets(raw_text) is True

    redacted = redact_secrets(raw_text)
    assert gemini_key not in redacted
    assert groq_key not in redacted
    assert cf_key not in redacted
    assert openai_key not in redacted
    assert "[REDACTED]" in redacted


def test_secret_redactor_masks_db_urls_and_passwords():
    db_url = "postgresql://dbuser:supersecretpass123@db.prod.internal:5432/analytics"
    raw_error = f"FATAL: connection failed for {db_url} password='secret_pwd_999'"

    assert detect_secrets(raw_error) is True
    clean = redact_secrets(raw_error)

    assert "supersecretpass123" not in clean
    assert "secret_pwd_999" not in clean
    assert "[REDACTED]" in clean


def test_secret_redactor_recursive_sanitization():
    payload = {
        "status": "error",
        "api_key": "AQ.MOCK_TEST_SAMPLE_secret",
        "meta": {
            "token": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.do_not_leak_this",
            "safe_field": 42,
        },
    }
    clean = SecretRedactor.sanitize_recursive(payload)
    assert clean["api_key"] == "[REDACTED]"
    assert clean["meta"]["safe_field"] == 42
    assert "do_not_leak_this" not in str(clean)


# =====================================================================
# 2. PII REDACTION TESTS
# =====================================================================

def test_pii_redactor_masks_emails_and_phones():
    text = "User john.doe@example.com with phone +1 (555) 234-5678 failed validation"
    assert detect_pii(text) is True
    clean = redact_pii(text)
    assert "john.doe@example.com" not in clean
    assert "555" not in clean
    assert "[EMAIL_REDACTED]" in clean or "[REDACTED]" in clean


def test_pii_redactor_masks_row_identity():
    bad_msg = "Row 47291 belonging to John Doe failed because target was null."
    clean = redact_pii(bad_msg)
    assert "Row 47291 belonging to John Doe failed" not in clean
    assert "One record failed validation because" in clean


# =====================================================================
# 3. OUTPUT SECURITY GATE & CONTEXT SANITIZATION
# =====================================================================

def test_output_security_gate_strips_tracebacks_and_paths():
    tb_text = (
        "Traceback (most recent call last):\n"
        '  File "C:\\Users\\Chokha\\AppData\\Local\\secret_path\\test.py", line 42, in <module>\n'
        "ValueError: Invalid configuration\n"
    )
    sanitized = OutputSecurityGate.sanitize_text(tb_text)
    assert "C:\\Users\\Chokha" not in sanitized
    assert "Traceback (most recent call last)" not in sanitized
    assert "hidden for security" in sanitized


def test_output_security_gate_notebook_sanitizer():
    nb = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["import os\n", 'API_KEY = "AQ.MOCK_TEST_SAMPLE_secret"\n'],
                "outputs": [{"text": ["Model trained with key AQ.MOCK_TEST_SAMPLE_secret\n"]}],
            }
        ]
    }
    cleaned_nb = OutputSecurityGate.sanitize_notebook(nb)
    nb_str = json.dumps(cleaned_nb)
    assert "AQ.MOCK_TEST_SAMPLE_secret" not in nb_str
    assert "[REDACTED]" in nb_str


# =====================================================================
# 4. ERROR DETECTOR & CLASSIFIER TESTS
# =====================================================================

def test_error_detector_normalizes_exception_without_leaks():
    secret_key = "AQ.MOCK_TEST_SAMPLE_secret_key_123"
    raw_exc = ValueError(f"Failed to connect to API using key {secret_key}")

    err_obj = ErrorDetector.detect_and_normalize(
        exception=raw_exc,
        stage="llm_invocation",
        agent_id="ml_strategy_agent",
    )
    assert err_obj.secret_detected is True
    assert secret_key not in err_obj.message
    assert secret_key not in err_obj.safe_message
    assert err_obj.error_id.startswith("ERR-")


def test_error_classifier_categories_and_codes():
    # 1. Transient rate limit
    e1 = ErrorDetector.detect_and_normalize(Exception("Rate limit 429 too many requests"))
    c1 = ErrorClassifier.classify(e1)
    assert c1.category == ErrorCategory.RATE_LIMIT
    assert c1.retryable is True
    assert c1.error_code == ErrorCode.ERR_RATE_LIMIT

    # 2. KNNImputer categorical dtype clash
    e2 = ErrorDetector.detect_and_normalize(Exception("KNNImputer could not convert string to float: 'Male'"))
    c2 = ErrorClassifier.classify(e2)
    assert c2.category == ErrorCategory.DATA_FORMAT
    assert c2.retryable is False
    assert c2.recoverable is True
    assert c2.error_code == ErrorCode.ERR_PREPROCESSING_FAILED

    # 3. Memory limit
    e3 = ErrorDetector.detect_and_normalize(MemoryError("Unable to allocate 16.0 GiB for an array"))
    c3 = ErrorClassifier.classify(e3)
    assert c3.category == ErrorCategory.MEMORY
    assert c3.severity == ErrorSeverity.CRITICAL
    assert c3.error_code == ErrorCode.ERR_RESOURCE_LIMIT


# =====================================================================
# 5. ROOT CAUSE ANALYZER & PLANNING TESTS
# =====================================================================

def test_root_cause_diagnoses_knnimputer_categorical_conflict():
    err = ErrorDetector.detect_and_normalize("KNNImputer failed because dataset contains unsupported string values")
    classified = ErrorClassifier.classify(err)
    report = RootCauseAnalyzer.analyze(classified)

    assert report.confidence == "HIGH"
    assert report.suggested_recovery_type == "PIPELINE_REPAIR_SPLIT_COLUMNS"
    assert "Categorical features were passed into a numerical-only transformer" in report.primary_cause

    plan = RecoveryPlanner.plan(classified, report)
    assert plan.strategy_name == "SEPARATE_NUMERICAL_CATEGORICAL_PIPELINE"
    assert plan.action_type == "REPAIR"


def test_root_cause_diagnoses_single_class_target():
    err = ErrorDetector.detect_and_normalize("The number of classes has to be greater than one; got 1 class")
    classified = ErrorClassifier.classify(err)
    report = RootCauseAnalyzer.analyze(classified)

    assert report.confidence == "HIGH"
    assert report.suggested_recovery_type == "USER_ACTION_REQUIRED"
    assert report.requires_human_intervention is True

    plan = RecoveryPlanner.plan(classified, report)
    assert plan.action_type == "ASK_USER"


# =====================================================================
# 6. BOUNDED RETRIES, LOOP DETECTION & CIRCUIT BREAKER
# =====================================================================

def test_retry_manager_bounds_and_loop_prevention():
    mgr = RetryManager()
    wf_id = "test_wf_001"
    agent_id = "agent_a"
    sig = "connection_timeout_error"
    strategy = "EXPONENTIAL_BACKOFF"

    # Attempt 1: Allowed
    allowed, state, reason = mgr.evaluate_retry_eligibility(wf_id, agent_id, sig, strategy, attempt_count=1)
    assert allowed is True
    assert state == RecoveryDecisionState.RETRY_REQUIRED

    # Duplicate state: Agent Loop Detection halts
    allowed_loop, state_loop, reason_loop = mgr.evaluate_retry_eligibility(wf_id, agent_id, sig, strategy, attempt_count=2)
    assert allowed_loop is False
    assert state_loop == RecoveryDecisionState.SAFE_STOP
    assert "loop detected" in reason_loop

    # Attempt count exceeded
    allowed_max, state_max, reason_max = mgr.evaluate_retry_eligibility(
        wf_id, agent_id, "different_error", "different_strategy", attempt_count=MAX_RECOVERY_ATTEMPTS + 1
    )
    assert allowed_max is False
    assert state_max == RecoveryDecisionState.UNRECOVERABLE


def test_circuit_breaker_transitions():
    cb = CircuitBreaker("test_service", failure_threshold=2, cooldown_seconds=0.1)
    assert cb.can_execute() is True

    cb.record_failure()
    assert cb.can_execute() is True

    cb.record_failure()  # Reaches threshold 2 -> OPEN
    assert cb.can_execute() is False

    import time
    time.sleep(0.15)
    # After cooldown -> HALF_OPEN
    assert cb.can_execute() is True
    cb.record_success()
    # After success -> CLOSED
    assert cb.state.value == "CLOSED"


# =====================================================================
# 7. RECOVERY EXECUTION & INDEPENDENT VALIDATION TESTS
# =====================================================================

def test_recovery_executor_repairs_preprocessing_pipeline():
    # Construct a problematic mixed dataframe
    df = pd.DataFrame({
        "age": [25.0, 30.0, np.nan, 45.0],
        "gender": ["Male", "Female", "Female", None],
    })

    plan = RecoveryPlan(
        error_id="ERR-101",
        strategy_name="SEPARATE_NUMERICAL_CATEGORICAL_PIPELINE",
        action_type="REPAIR",
        confidence="HIGH",
    )
    err = ErrorDetector.detect_and_normalize("could not convert string to float: 'Male'")

    decision, updated_state, val_report = RecoveryExecutor.execute_plan(
        plan=plan,
        error_obj=err,
        current_state={"df": df},
    )

    assert decision == RecoveryDecisionState.RECOVERED
    assert val_report.is_valid is True
    assert "preprocessor" in updated_state
    # Check that the preprocessor can transform the dataframe without throwing
    out = updated_state["preprocessor"].transform(df)
    assert out is not None
    assert len(out) == 4


def test_recovery_executor_adaptive_resource_reduction():
    plan = RecoveryPlan(
        error_id="ERR-102",
        strategy_name="ADAPTIVE_RESOURCE_REDUCTION",
        action_type="REPAIR",
        confidence="HIGH",
    )
    err = ErrorDetector.detect_and_normalize(MemoryError("OOM during model training"))

    decision, updated_state, val_report = RecoveryExecutor.execute_plan(
        plan=plan,
        error_obj=err,
        current_state={"is_classification": True},
    )
    assert decision == RecoveryDecisionState.RECOVERED
    assert val_report.is_valid is True
    assert updated_state["model_name"] == "HistGradientBoosting"


# =====================================================================
# 8. ROLLBACK MANAGER & CHECKPOINTS
# =====================================================================

def test_rollback_manager_checkpoints():
    rb = RollbackManager()
    wf_id = "wf_checkpoint_test"

    rb.save_checkpoint(wf_id, "data_ingestion", {"data": "loaded"})
    rb.save_checkpoint(wf_id, "preprocessing", {"pipeline": "built"})
    rb.save_checkpoint(wf_id, "baseline_training", {"model": "trained"})

    # If evaluation fails, rollback should return baseline_training checkpoint
    nearest = rb.get_nearest_safe_checkpoint(wf_id, failed_stage="evaluation")
    assert nearest is not None
    assert nearest.checkpoint_id == "checkpoint_6_baseline_complete"
    assert nearest.state_payload["model"] == "trained"


# =====================================================================
# 9. RECOVERY AGENTS INTEGRATION TESTS
# =====================================================================

def test_fallback_supervisor_agent():
    agent = FallbackSupervisorAgent(session_id="session_supervisor_test")
    out = agent.run(AgentInput(
        session_id="session_supervisor_test",
        parameters={
            "error": "KNNImputer non-numeric string encountered in column 'category'",
            "stage": "preprocessing",
            "agent_id": "preprocessing_agent",
        },
    ))
    assert out.status in ("success", "warning")
    assert "error_id" in out.data
    assert "user_panel" in out.data


def test_confidentiality_agent_redacts_payload():
    agent = ConfidentialityAgent(session_id="conf_session")
    secret_payload = {
        "status": "failed",
        "key": "AQ.MOCK_TEST_SAMPLE_dummy_token",
        "email": "admin@datawise.io",
    }
    out = agent.run(AgentInput(
        session_id="conf_session",
        parameters={"content": secret_payload},
    ))
    assert out.status == "success"
    clean_data = out.data["sanitized_content"]
    assert clean_data["key"] == "[REDACTED]"
    assert clean_data["email"] in ("[EMAIL_REDACTED]", "[PII_REDACTED]")


def test_all_12_recovery_agents_instantiation_and_run():
    # Verify every required agent runs cleanly
    input_sample = AgentInput(session_id="test_suite_all", parameters={"error": "Test transient error"})

    agents = [
        FallbackSupervisorAgent(),
        ErrorDetectionAgent(),
        ErrorClassificationAgent(),
        RootCauseAgent(),
        RecoveryPlanningAgent(),
        RecoveryExecutionAgent(),
        RetryDecisionAgent(),
        ValidationAgent(),
        RollbackAgent(),
        EscalationAgent(),
        ConfidentialityAgent(),
        ErrorExplanationAgent(),
    ]
    for ag in agents:
        res = ag.run(input_sample)
        assert res.agent_name is not None
        assert res.status in ("success", "warning", "needs_approval", "error")


# =====================================================================
# 10. RECOVERY GRAPH LANGGRAPH COMPILED TEST
# =====================================================================

def test_recovery_graph_execution():
    compiled_graph = build_recovery_graph()
    initial_state: RecoveryState = {
        "session_id": "test_graph_session",
        "workflow_id": "test_graph_wf",
        "error_raw": "KNNImputer could not convert string to float: 'CategoryA'",
        "stage": "preprocessing",
        "agent_id": "preprocessing_execution_agent",
        "attempt_count": 1,
        "system_state": {
            "df": pd.DataFrame({"num": [1.0, 2.0], "cat": ["A", "B"]})
        },
    }

    final_state = compiled_graph.invoke(initial_state)
    assert final_state is not None
    assert "error_obj" in final_state
    assert "decision" in final_state
    assert "api_response" in final_state
    assert final_state["api_response"]["success"] in (True, False)
    assert "id" in final_state["api_response"]["error"]
