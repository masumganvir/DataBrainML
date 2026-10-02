"""
DataWise AI — Recovery Graph (LangGraph Section 59 & 60)
Governs error detection, classification, root cause analysis, security gates,
bounded planning, decision routing, independent validation, and safe resumption.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict
from loguru import logger
from langgraph.graph import END, StateGraph

from recovery.context_sanitizer import OutputSecurityGate
from recovery.error_classifier import ErrorClassifier
from recovery.error_detector import ErrorDetector, ErrorObject
from recovery.policies import (
    MAX_RECOVERY_ATTEMPTS,
    ErrorCode,
    ErrorSeverity,
    RecoveryDecisionState,
)
from recovery.recovery_executor import RecoveryExecutor
from recovery.recovery_planner import RecoveryPlan, RecoveryPlanner
from recovery.root_cause_analyzer import RootCauseAnalyzer, RootCauseReport
from recovery.safe_error_formatter import SafeErrorFormatter
from recovery.validation_manager import ValidationManager, ValidationReport


class RecoveryState(TypedDict, total=False):
    """LangGraph state schema for recovery graph execution."""
    session_id: str
    workflow_id: str
    error_raw: Any
    stage: str
    agent_id: str
    node_id: str
    attempt_count: int
    error_obj: Dict[str, Any]
    root_cause: Dict[str, Any]
    plan: Dict[str, Any]
    decision: str
    is_validated: bool
    validation_report: Dict[str, Any]
    system_state: Dict[str, Any]
    safe_message: str
    user_panel: str
    api_response: Dict[str, Any]
    can_resume: bool
    should_pause: bool


def error_detector_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 1. Detecting and sanitizing error")
    err_obj = ErrorDetector.detect_and_normalize(
        exception=state.get("error_raw", "Unknown error"),
        stage=state.get("stage", "execution"),
        agent_id=state.get("agent_id", "unknown_agent"),
        node_id=state.get("node_id", "unknown_node"),
        workflow_id=state.get("workflow_id", state.get("session_id", "default_workflow")),
        attempt_count=state.get("attempt_count", 1),
        context=state.get("system_state", {}),
    )
    return {
        **state,
        "error_obj": err_obj.model_dump(),
        "safe_message": err_obj.safe_message,
    }


def classifier_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 2. Classifying error category and severity")
    err_obj = ErrorObject(**state["error_obj"])
    classified = ErrorClassifier.classify(err_obj)
    return {
        **state,
        "error_obj": classified.model_dump(),
    }


def root_cause_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 3. Performing diagnostic root cause analysis")
    err_obj = ErrorObject(**state["error_obj"])
    cause_report = RootCauseAnalyzer.analyze(err_obj, state.get("system_state", {}))
    return {
        **state,
        "root_cause": cause_report.model_dump(),
    }


def security_check_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 4. Enforcing security gate")
    err_obj = ErrorObject(**state["error_obj"])
    if err_obj.secret_detected or err_obj.category.value == "SECURITY":
        panel = SafeErrorFormatter.format_user_panel(
            error_id=err_obj.error_id,
            status=RecoveryDecisionState.SECURITY_STOP,
            stage=state.get("stage", "execution"),
            what_happened="Processing halted by security boundary.",
            reason="A confidential token or security violation was detected.",
            recovery_attempted="Operation blocked to protect credentials.",
            recovery_result="Security halt enforced.",
            recommended_action="Remove credentials from dataset and inspect input.",
            reference_id=err_obj.error_id,
        )
        api_resp = SafeErrorFormatter.format_security_incident_response(err_obj.error_id)
        return {
            **state,
            "decision": RecoveryDecisionState.SECURITY_STOP.value,
            "can_resume": False,
            "should_pause": True,
            "user_panel": panel,
            "api_response": api_resp,
        }
    return state


def recovery_planner_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 5. Formulating recovery plan")
    current_attempts = state.get("attempt_count", 0) + 1
    err_obj = ErrorObject(**state["error_obj"])
    cause = RootCauseReport(**state["root_cause"])
    plan = RecoveryPlanner.plan(err_obj, cause)
    return {
        **state,
        "attempt_count": current_attempts,
        "plan": plan.model_dump(),
        "decision": plan.action_type,
    }


def execution_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 6. Executing recovery plan")
    plan = RecoveryPlan(**state["plan"])
    err_obj = ErrorObject(**state["error_obj"])
    current_sys_state = state.get("system_state", {})

    decision, updated_state, val_report = RecoveryExecutor.execute_plan(
        plan=plan,
        error_obj=err_obj,
        current_state=current_sys_state,
    )

    return {
        **state,
        "decision": decision.value,
        "system_state": updated_state if val_report.is_valid else current_sys_state,
        "is_validated": val_report.is_valid,
        "validation_report": val_report.model_dump(),
        "can_resume": val_report.is_valid,
    }


def validation_node(state: RecoveryState) -> RecoveryState:
    logger.info("[RecoveryGraph] 7. Independent validation check")
    is_valid = state.get("is_validated", False)
    val_report = state.get("validation_report", {})
    err_obj = ErrorObject(**state.get("error_obj", {}))
    plan = state.get("plan", {})

    panel = SafeErrorFormatter.format_user_panel(
        error_id=err_obj.error_id,
        status=state.get("decision", "SAFE_STOP"),
        stage=state.get("stage", "execution"),
        what_happened=f"Failure during {state.get('stage', 'execution')}.",
        reason=state.get("root_cause", {}).get("primary_cause", "Internal exception"),
        recovery_attempted=plan.get("strategy_name", "Safe recovery"),
        recovery_result="Validation passed." if is_valid else "Validation failed.",
        recommended_action=err_obj.recommended_action,
        reference_id=err_obj.error_id,
    )
    api_resp = SafeErrorFormatter.format_api_response(
        error_id=err_obj.error_id,
        error_code=err_obj.error_code,
        message=err_obj.safe_message,
        hint=err_obj.recommended_action,
        retryable=not is_valid and (state.get("attempt_count", 1) < MAX_RECOVERY_ATTEMPTS),
        status=state.get("decision", "SAFE_STOP"),
    )

    return {
        **state,
        "can_resume": is_valid,
        "user_panel": panel,
        "api_response": api_resp,
    }


def escalation_node(state: RecoveryState) -> RecoveryState:
    logger.warning("[RecoveryGraph] 8. Bounded limit reached - Escalating to human operator")
    err_obj = ErrorObject(**state.get("error_obj", {}))
    panel = SafeErrorFormatter.format_user_panel(
        error_id=err_obj.error_id,
        status=RecoveryDecisionState.SAFE_STOP,
        stage=state.get("stage", "execution"),
        what_happened="Recovery threshold exceeded.",
        reason="Automated recovery could not be safely validated within bounds.",
        recovery_attempted=f"{state.get('attempt_count', 1)} attempts completed.",
        recovery_result="Execution safely suspended.",
        recommended_action="Review error logs and provide user guidance.",
        reference_id=err_obj.error_id,
    )
    api_resp = SafeErrorFormatter.format_api_response(
        error_id=err_obj.error_id,
        error_code=err_obj.error_code,
        message="Workflow suspended after exceeding recovery attempts.",
        hint="Manual review required.",
        retryable=False,
        status=RecoveryDecisionState.SAFE_STOP.value,
    )
    return {
        **state,
        "can_resume": False,
        "should_pause": True,
        "decision": RecoveryDecisionState.SAFE_STOP.value,
        "user_panel": panel,
        "api_response": api_resp,
    }


# Conditional routing predicates
def route_security_check(state: RecoveryState) -> Literal["proceed", "security_stop"]:
    if state.get("decision") == RecoveryDecisionState.SECURITY_STOP.value:
        return "security_stop"
    return "proceed"


def route_validation_result(state: RecoveryState) -> Literal["resume", "retry_bounded", "escalate"]:
    if state.get("can_resume", False):
        return "resume"
    attempts = state.get("attempt_count", 1)
    if attempts >= MAX_RECOVERY_ATTEMPTS:
        return "escalate"
    return "retry_bounded"


def build_recovery_graph() -> StateGraph:
    """Builds and compiles the StateGraph for the Fallback & Recovery system."""
    graph = StateGraph(RecoveryState)

    graph.add_node("error_detector", error_detector_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("security_check", security_check_node)
    graph.add_node("planner", recovery_planner_node)
    graph.add_node("executor", execution_node)
    graph.add_node("validator", validation_node)
    graph.add_node("escalation", escalation_node)

    graph.set_entry_point("error_detector")
    graph.add_edge("error_detector", "classifier")
    graph.add_edge("classifier", "root_cause")
    graph.add_edge("root_cause", "security_check")

    graph.add_conditional_edges(
        "security_check",
        route_security_check,
        {
            "security_stop": END,
            "proceed": "planner",
        },
    )

    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "validator")

    graph.add_conditional_edges(
        "validator",
        route_validation_result,
        {
            "resume": END,
            "escalate": "escalation",
            "retry_bounded": "planner",
        },
    )

    graph.add_edge("escalation", END)

    return graph.compile()
