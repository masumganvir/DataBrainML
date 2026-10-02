"""
Recovery Planner
Formulates precise, multi-step, verified recovery plans based on Root Cause Reports.
Never performs blind identical retries for data, model, or memory errors.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from recovery.error_detector import ErrorObject
from recovery.root_cause_analyzer import RootCauseReport


class RecoveryPlan(BaseModel):
    """Actionable multi-step recovery plan."""
    plan_id: str = Field(default_factory=lambda: f"PLAN-{uuid.uuid4().hex[:8].upper()}")
    error_id: str
    strategy_name: str
    steps: List[str] = Field(default_factory=list)
    action_type: Literal[
        "RETRY",
        "FALLBACK",
        "REPAIR",
        "ROLLBACK",
        "ASK_USER",
        "SAFE_STOP",
        "SECURITY_STOP",
    ]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    estimated_cost: float = 0.0


class RecoveryPlanner:
    """Generates context-aware recovery plans tailored to the exact failure mode."""

    @classmethod
    def plan(cls, error_obj: ErrorObject, root_cause: RootCauseReport) -> RecoveryPlan:
        # 1. Security stops
        if root_cause.suggested_recovery_type == "SECURITY_STOP" or error_obj.secret_detected:
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="SECURITY_CIRCUIT_BREAKER_HALT",
                steps=[
                    "Stop current workflow immediately",
                    "Block all outgoing generated tokens or payload",
                    "Redact any sensitive traces from memory",
                    "Log security incident to audit store",
                    "Notify security monitor with sanitized ID",
                ],
                action_type="SECURITY_STOP",
                confidence="HIGH",
            )

        # 2. User action required (e.g. single class target, missing credentials)
        if root_cause.requires_human_intervention or root_cause.suggested_recovery_type == "USER_ACTION_REQUIRED":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="USER_INTERVENTION_REQUEST",
                steps=[
                    "Preserve current pipeline state checkpoint",
                    "Generate safe, actionable user guidance",
                    "Await user target column clarification or credential update",
                ],
                action_type="ASK_USER",
                confidence=root_cause.confidence,
            )

        # 3. Preprocessing / ColumnTransformer Categorical conflict (e.g. KNNImputer)
        if root_cause.suggested_recovery_type == "PIPELINE_REPAIR_SPLIT_COLUMNS":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="SEPARATE_NUMERICAL_CATEGORICAL_PIPELINE",
                steps=[
                    "Inspect feature dtypes and identify all categorical columns",
                    "Separate numerical and categorical sub-pipelines",
                    "Apply numerical imputer (KNN or median) strictly to numerical columns",
                    "Apply most_frequent/constant imputation to categorical columns",
                    "Rebuild ColumnTransformer assembly",
                    "Run independent transformation test on sample batch",
                    "Resume feature engineering stage",
                ],
                action_type="REPAIR",
                confidence="HIGH",
                parameters={"repair_action": "split_column_types"},
            )

        # 4. Out of Memory / Resource limits
        if root_cause.suggested_recovery_type == "DOWNSAMPLE_OR_LIGHT_ESTIMATOR":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="ADAPTIVE_RESOURCE_REDUCTION",
                steps=[
                    "Downsample training dataset to 50% or stratified sample",
                    "Reduce estimator complexity (max_depth=4, n_estimators=50)",
                    "Set parallel worker threads to single job (n_jobs=1)",
                    "Fallback to memory-efficient candidate (e.g. HistGradientBoosting)",
                    "Validate memory consumption on warm-up mini-batch",
                    "Resume model training",
                ],
                action_type="REPAIR",
                confidence="HIGH",
                parameters={"sample_fraction": 0.5, "n_jobs": 1},
            )

        # 5. LLM Provider failure (Gemini -> Groq -> Cloudflare -> Deterministic)
        if root_cause.suggested_recovery_type == "PROVIDER_FALLBACK":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="LLM_MULTI_PROVIDER_FALLBACK",
                steps=[
                    "Flag current primary LLM provider in circuit breaker cooldown",
                    "Route request to secondary tier (Groq or Cloudflare)",
                    "If all remote providers unavailable, activate deterministic Python rules",
                    "Verify response format and schema compliance",
                    "Resume agent reasoning node",
                ],
                action_type="FALLBACK",
                confidence="HIGH",
                parameters={"switch_provider": True},
            )

        # 6. MCP failure -> direct native connector
        if root_cause.suggested_recovery_type == "FALLBACK_DIRECT_CONNECTOR":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="MCP_TO_DIRECT_CONNECTOR_FALLBACK",
                steps=[
                    "Record MCP transport unavailability",
                    "Switch to built-in direct SQLAlchemy / asyncpg connector",
                    "Validate read-only query permissions",
                    "Resume database extraction without MCP dependency",
                ],
                action_type="FALLBACK",
                confidence="HIGH",
                parameters={"use_direct_connector": True},
            )

        # 7. Model Serialization failure
        if root_cause.suggested_recovery_type == "ALTERNATIVE_SERIALIZATION":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="RESILIENT_SERIALIZATION_PIPELINE",
                steps=[
                    "Inspect model object for unpickleable lambdas or local functions",
                    "Attempt cloudpickle with protocol version 5",
                    "If unpickling fails, export via ONNX runtime specification",
                    "Load exported artifact into clean memory space",
                    "Execute dummy prediction test to verify integrity",
                    "Store validated artifact in Model Registry",
                ],
                action_type="REPAIR",
                confidence="HIGH",
            )

        # 8. Transient / Rate Limit backoff
        if error_obj.retryable and root_cause.suggested_recovery_type == "EXPONENTIAL_BACKOFF_RETRY":
            return RecoveryPlan(
                error_id=error_obj.error_id,
                strategy_name="EXPONENTIAL_BACKOFF_WITH_JITTER",
                steps=[
                    "Calculate backoff delay (2^attempt + jitter)",
                    "Wait for backoff duration",
                    "Retry idempotent operation",
                ],
                action_type="RETRY",
                confidence="MEDIUM",
                parameters={"backoff_base": 2.0},
            )

        # Default safe stop if low confidence
        return RecoveryPlan(
            error_id=error_obj.error_id,
            strategy_name="PRESERVATION_SAFE_STOP",
            steps=[
                "Create checkpoint of current state",
                "Log unverified error condition",
                "Halt workflow safely without corrupting existing artifacts",
            ],
            action_type="SAFE_STOP",
            confidence="LOW",
        )
