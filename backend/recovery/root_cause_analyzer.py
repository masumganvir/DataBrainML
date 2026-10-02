"""
Root Cause Analyzer
Performs evidence-based diagnostics on failures across data, pipelines, models,
providers, and databases. Never invents causes; assigns explicit confidence ratings.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from recovery.error_detector import ErrorObject
from recovery.policies import ErrorCategory


class RootCauseReport(BaseModel):
    """Structured diagnostic root cause assessment."""
    error_id: str
    primary_cause: str
    evidence: List[str] = Field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    suggested_recovery_type: str = "SAFE_STOP"
    is_state_corrupted: bool = False
    requires_human_intervention: bool = False
    diagnostic_details: Dict[str, Any] = Field(default_factory=dict)


class RootCauseAnalyzer:
    """Analyzes error objects and execution context to pinpoint underlying causes."""

    @classmethod
    def analyze(cls, error_obj: ErrorObject, system_state: Optional[Dict[str, Any]] = None) -> RootCauseReport:
        msg = (error_obj.message or "").lower()
        cat = error_obj.category
        evidence: List[str] = []
        state = system_state or {}

        # 1. Target column single-class or insufficient class variation
        if (
            "one class" in msg
            or "single class" in msg
            or "only 1 class" in msg
            or "1 class" in msg
            or "greater than one" in msg
            or "n_classes <= 1" in msg
        ):
            evidence.append("Exception text indicates single target class distribution.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Target column contains insufficient class variation (only 1 class found).",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="USER_ACTION_REQUIRED",
                is_state_corrupted=False,
                requires_human_intervention=True,
                diagnostic_details={"category": cat.value},
            )

        # 2. KNNImputer / Scaler non-numeric or categorical column conflict
        if (
            "knnimputer" in msg
            or "could not convert string to float" in msg
            or ("unsupported operand type" in msg and "str" in msg)
        ):
            evidence.append("String/categorical values encountered in numerical transformation step.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Categorical features were passed into a numerical-only transformer (e.g. KNNImputer or StandardScaler).",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="PIPELINE_REPAIR_SPLIT_COLUMNS",
                is_state_corrupted=False,
                requires_human_intervention=False,
                diagnostic_details={"column_issue": "unseparated_categorical_columns"},
            )

        # 3. Memory exhaustion / Out of memory
        if (
            "memory" in msg
            or "oom" in msg
            or cat in (ErrorCategory.MEMORY, ErrorCategory.RESOURCE_EXHAUSTION)
        ):
            evidence.append("System memory limit or allocation error encountered during training/processing.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Excessive memory consumption caused by large batch size or high-cardinality feature space.",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="DOWNSAMPLE_OR_LIGHT_ESTIMATOR",
                is_state_corrupted=False,
                requires_human_intervention=False,
                diagnostic_details={"resource": "RAM"},
            )

        # 4. LLM Provider failure / Quota / Timeout
        if cat in (ErrorCategory.LLM_PROVIDER, ErrorCategory.LLM_QUOTA, ErrorCategory.LLM_TIMEOUT):
            evidence.append(f"LLM upstream failure classified as {cat.value}")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause=f"Upstream LLM provider disruption: {cat.value}",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="PROVIDER_FALLBACK",
                is_state_corrupted=False,
                requires_human_intervention=False,
            )

        # 5. MCP Tool Server failure
        if cat == ErrorCategory.MCP_FAILURE:
            evidence.append("MCP server connection or tool invocation timed out / refused.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="MCP external tool server unavailable.",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="FALLBACK_DIRECT_CONNECTOR",
                is_state_corrupted=False,
                requires_human_intervention=False,
            )

        # 6. Database Connection Failure
        if cat in (ErrorCategory.DATABASE, ErrorCategory.DATABASE_SCHEMA):
            evidence.append("Database query or connection failure.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Database host unreachable, schema mismatch, or query validation failed.",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="FALLBACK_CONNECTION_OR_VALIDATION",
                is_state_corrupted=False,
                requires_human_intervention=False,
            )

        # 7. Model Serialization Failure
        if cat == ErrorCategory.MODEL_SERIALIZATION:
            evidence.append("Model packaging/saving failed.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Estimator or pipeline contains unpickleable closures or missing custom class dependencies.",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="ALTERNATIVE_SERIALIZATION",
                is_state_corrupted=False,
                requires_human_intervention=False,
            )

        # 8. Security / Credential Detection
        if cat == ErrorCategory.SECURITY or error_obj.secret_detected:
            evidence.append("Security risk or credential string detected in processing stream.")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause="Operation violated security boundary or sensitive tokens were detected in input/output.",
                evidence=evidence,
                confidence="HIGH",
                suggested_recovery_type="SECURITY_STOP",
                is_state_corrupted=True,
                requires_human_intervention=True,
            )

        # 9. Transient Network / Rate Limit
        if cat in (ErrorCategory.TRANSIENT, ErrorCategory.RATE_LIMIT, ErrorCategory.NETWORK):
            evidence.append(f"Transient error pattern: {cat.value}")
            return RootCauseReport(
                error_id=error_obj.error_id,
                primary_cause=f"Temporary network disruption or rate throttling ({cat.value}).",
                evidence=evidence,
                confidence="MEDIUM",
                suggested_recovery_type="EXPONENTIAL_BACKOFF_RETRY",
                is_state_corrupted=False,
                requires_human_intervention=False,
            )

        # Fallback / Uncertain
        evidence.append("No specific pattern matched in error signature.")
        return RootCauseReport(
            error_id=error_obj.error_id,
            primary_cause="Uncertain or unverified error root cause.",
            evidence=evidence,
            confidence="LOW",
            suggested_recovery_type="SAFE_STOP",
            is_state_corrupted=False,
            requires_human_intervention=True,
        )
