"""
Error Classifier
Classifies raw ErrorObjects into precise categories, assigns severity,
evaluates retryability/recoverability, and maps to standardized error codes.
"""

from __future__ import annotations

import re
from typing import Tuple
from recovery.policies import (
    ErrorCategory,
    ErrorCode,
    ErrorSeverity,
    RETRYABLE_CATEGORIES,
    SECURITY_HALT_CATEGORIES,
)
from recovery.error_detector import ErrorObject


class ErrorClassifier:
    """Classifies errors based on exception type, message patterns, and execution stage."""

    @classmethod
    def classify(cls, error_obj: ErrorObject) -> ErrorObject:
        """Enriches the ErrorObject with classification, severity, error code, and retry flags."""
        category, severity, code, action = cls._determine_classification(error_obj)

        error_obj.category = category
        error_obj.severity = severity
        error_obj.error_code = code
        error_obj.recommended_action = action

        # Determine retryable / recoverable
        if category in SECURITY_HALT_CATEGORIES or error_obj.secret_detected:
            error_obj.retryable = False
            error_obj.recoverable = False
            error_obj.severity = ErrorSeverity.SECURITY_CRITICAL
            error_obj.safe_message = "A security or permission check halted the requested operation."
            error_obj.user_safe = True
        elif category in RETRYABLE_CATEGORIES:
            error_obj.retryable = True
            error_obj.recoverable = True
        else:
            error_obj.retryable = False
            # Most domain errors (data/model/feature) are recoverable via pipeline adaptation
            error_obj.recoverable = True

        return error_obj

    @classmethod
    def _determine_classification(
        cls, error_obj: ErrorObject
    ) -> Tuple[ErrorCategory, ErrorSeverity, ErrorCode, str]:
        msg = (error_obj.message or "").lower()
        exc_name = (error_obj.raw_exception_name or "").lower()
        stage = (error_obj.stage or "").lower()

        # 1. Security / Credentials / Injection / Secret detected
        if (
            error_obj.secret_detected
            or "api_key" in msg
            or "unauthorized" in msg
            or "forbidden" in msg
            or "permission denied" in msg
            or "prompt injection" in msg
            or "token expired" in msg
        ):
            if "unauthorized" in msg or "401" in msg:
                return (
                    ErrorCategory.AUTHENTICATION,
                    ErrorSeverity.HIGH,
                    ErrorCode.ERR_DATABASE_PERMISSION,
                    "Verify service authentication credentials and re-authenticate.",
                )
            if "forbidden" in msg or "403" in msg or "permission denied" in msg:
                return (
                    ErrorCategory.AUTHORIZATION,
                    ErrorSeverity.HIGH,
                    ErrorCode.ERR_DATABASE_PERMISSION,
                    "Ensure current identity holds necessary permissions.",
                )
            return (
                ErrorCategory.SECURITY,
                ErrorSeverity.SECURITY_CRITICAL,
                ErrorCode.ERR_SECURITY_BLOCKED,
                "Workflow halted due to security violation or credential detection.",
            )

        # 2. Rate Limits & Quotas
        if "rate limit" in msg or "429" in msg or "too many requests" in msg or "quota" in msg:
            if "quota" in msg:
                return (
                    ErrorCategory.LLM_QUOTA,
                    ErrorSeverity.HIGH,
                    ErrorCode.ERR_LLM_QUOTA,
                    "Provider quota exhausted. Switch to configured fallback provider.",
                )
            return (
                ErrorCategory.RATE_LIMIT,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_RATE_LIMIT,
                "Rate limit hit. Applying exponential backoff with jitter.",
            )

        # 3. Timeouts & Network
        if "timeout" in msg or "timed out" in msg or "timeouterror" in exc_name:
            if "llm" in stage or "gemini" in msg or "groq" in msg or "cloudflare" in msg:
                return (
                    ErrorCategory.LLM_TIMEOUT,
                    ErrorSeverity.RECOVERABLE,
                    ErrorCode.ERR_LLM_TIMEOUT,
                    "LLM request timed out. Retrying with adjusted timeout or fallback provider.",
                )
            return (
                ErrorCategory.TIMEOUT,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_LLM_TIMEOUT,
                "Network request timed out. Retrying with controlled timeout adjustment.",
            )

        if "connection" in msg or "connecterror" in exc_name or "dns" in msg or "econnrefused" in msg:
            if "db" in stage or "database" in stage or "postgres" in msg:
                return (
                    ErrorCategory.DATABASE,
                    ErrorSeverity.HIGH,
                    ErrorCode.ERR_DATABASE_CONNECTION,
                    "Database unreachable. Check network status and failover connections.",
                )
            return (
                ErrorCategory.NETWORK,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_DATABASE_CONNECTION,
                "Transient network failure detected. Retrying with backoff.",
            )

        # 4. Resource limits (Memory, CPU, Disk)
        if "outofmemory" in exc_name or "memoryerror" in exc_name or "oom" in msg or "out of memory" in msg:
            return (
                ErrorCategory.MEMORY,
                ErrorSeverity.CRITICAL,
                ErrorCode.ERR_RESOURCE_LIMIT,
                "Memory threshold exceeded. Downsample data, chunk processing, or select lighter estimator.",
            )

        # 5. MCP Failure
        if "mcp" in stage or "mcp" in msg or "tool server" in msg:
            return (
                ErrorCategory.MCP_FAILURE,
                ErrorSeverity.HIGH,
                ErrorCode.ERR_MCP_UNAVAILABLE,
                "MCP server unavailable. Switching to direct native connector.",
            )

        # 6. Model Training & Serialization
        if (
            "one class" in msg
            or "single class" in msg
            or "insufficient class" in msg
            or "1 class" in msg
            or "greater than one" in msg
        ):
            return (
                ErrorCategory.MODEL_TRAINING,
                ErrorSeverity.CRITICAL,
                ErrorCode.ERR_MODEL_TRAINING_FAILED,
                "Target contains only one class. Provide samples with multiple classes.",
            )

        if "model" in stage or "train" in stage or "estimator" in msg or "classifier" in msg or "regressor" in msg:
            if "pickle" in msg or "joblib" in msg or "serialization" in msg or "save" in msg:
                return (
                    ErrorCategory.MODEL_SERIALIZATION,
                    ErrorSeverity.HIGH,
                    ErrorCode.ERR_MODEL_SERIALIZATION_FAILED,
                    "Serialization failed. Verify dependencies and attempt alternative serialization format.",
                )
            return (
                ErrorCategory.MODEL_TRAINING,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_MODEL_TRAINING_FAILED,
                "Estimator failed. Evaluate candidate compatibility or adjust hyperparameters.",
            )

        # 7. Preprocessing & Feature Engineering
        if "knnimputer" in msg or "nan" in msg or "could not convert" in msg or "dtype" in msg or "categorical" in msg:
            return (
                ErrorCategory.DATA_FORMAT,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_PREPROCESSING_FAILED,
                "Incompatible feature types detected. Separate numerical and categorical pipelines.",
            )

        if "feature" in stage or "preprocess" in stage:
            return (
                ErrorCategory.FEATURE_ENGINEERING,
                ErrorSeverity.RECOVERABLE,
                ErrorCode.ERR_FEATURE_ENGINEERING_FAILED,
                "Feature transformation failed. Fallback to robust imputation and standard encoding.",
            )

        # 8. Data Quality & Format
        if "empty" in msg or "no columns" in msg or "unsupported file" in msg:
            return (
                ErrorCategory.DATA_FORMAT,
                ErrorSeverity.CRITICAL,
                ErrorCode.ERR_DATA_INVALID,
                "Dataset format is invalid or empty. Provide a valid CSV/Excel/Parquet file.",
            )

        # 9. Drift & Validation
        if "drift" in stage or "drift" in msg:
            return (
                ErrorCategory.DRIFT,
                ErrorSeverity.WARNING,
                ErrorCode.ERR_DRIFT_DETECTED,
                "Data or concept drift detected. Trigger safe model retraining.",
            )

        if "validation" in stage or "schema" in msg:
            return (
                ErrorCategory.VALIDATION,
                ErrorSeverity.HIGH,
                ErrorCode.ERR_SCHEMA_MISMATCH,
                "Schema validation mismatch. Verify column names and datatypes.",
            )

        # Default fallback
        return (
            ErrorCategory.UNKNOWN,
            ErrorSeverity.RECOVERABLE,
            ErrorCode.ERR_UNKNOWN,
            "Diagnose failure context and attempt safe recovery or checkpoint resume.",
        )
