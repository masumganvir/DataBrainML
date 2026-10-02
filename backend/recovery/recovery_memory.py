"""
Recovery Memory
Persists verified, validated recovery patterns for rapid, confident future resolution.
Never learns blindly from failures and strictly prohibits storing secrets or raw data.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from recovery.context_sanitizer import OutputSecurityGate


class RecoveryPattern(BaseModel):
    pattern_id: str
    error_signature: str
    solution_strategy: str
    validation_standard: str
    success_count: int = 1
    total_applications: int = 1
    version: int = 1
    applicable_context: Dict[str, Any] = Field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.total_applications == 0:
            return 1.0
        return self.success_count / self.total_applications


class RecoveryMemory:
    """Stores validated recovery patterns that have successfully passed validation."""

    def __init__(self):
        # Initial core catalog of verified, safe automated recovery patterns
        self._patterns: Dict[str, RecoveryPattern] = {
            "knnimputer_categorical": RecoveryPattern(
                pattern_id="PAT-001",
                error_signature="knnimputer_non_numeric",
                solution_strategy="SEPARATE_NUMERICAL_CATEGORICAL_PIPELINE",
                validation_standard="preprocessing_validation",
                success_count=10,
                total_applications=10,
                version=1,
                applicable_context={"stage": "preprocessing"},
            ),
            "xgboost_oom": RecoveryPattern(
                pattern_id="PAT-002",
                error_signature="estimator_memory_limit",
                solution_strategy="ADAPTIVE_RESOURCE_REDUCTION",
                validation_standard="model_validation",
                success_count=8,
                total_applications=8,
                version=1,
                applicable_context={"stage": "training"},
            ),
            "mcp_server_offline": RecoveryPattern(
                pattern_id="PAT-003",
                error_signature="mcp_unavailable",
                solution_strategy="MCP_TO_DIRECT_CONNECTOR_FALLBACK",
                validation_standard="database_validation",
                success_count=5,
                total_applications=5,
                version=1,
                applicable_context={"stage": "data_ingestion"},
            ),
        }

    def match_pattern(self, error_message: str, stage: str = "") -> Optional[RecoveryPattern]:
        """Finds an existing verified recovery pattern matching the error message."""
        msg_clean = OutputSecurityGate.sanitize_text(error_message).lower()

        if "knnimputer" in msg_clean or ("convert string to float" in msg_clean and "preprocess" in stage.lower()):
            return self._patterns.get("knnimputer_categorical")
        if "memory" in msg_clean or "oom" in msg_clean:
            return self._patterns.get("xgboost_oom")
        if "mcp" in msg_clean or "mcp" in stage.lower():
            return self._patterns.get("mcp_server_offline")

        return None

    def record_validated_pattern(
        self,
        error_signature: str,
        solution_strategy: str,
        validation_standard: str,
        is_successful: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Records or updates a recovery pattern.
        Only validated recoveries increase the success count.
        """
        # Strictly sanitize inputs before storing in memory
        sig = OutputSecurityGate.sanitize_text(error_signature)
        strat = OutputSecurityGate.sanitize_text(solution_strategy)
        val = OutputSecurityGate.sanitize_text(validation_standard)
        clean_ctx = OutputSecurityGate.sanitize(context or {})

        key = f"{sig}_{strat}"
        if key in self._patterns:
            pat = self._patterns[key]
            pat.total_applications += 1
            if is_successful:
                pat.success_count += 1
        elif is_successful:
            # Only create new patterns if they were independently verified as successful
            self._patterns[key] = RecoveryPattern(
                pattern_id=f"PAT-{len(self._patterns) + 1:03d}",
                error_signature=sig,
                solution_strategy=strat,
                validation_standard=val,
                success_count=1,
                total_applications=1,
                applicable_context=clean_ctx,
            )

    def list_patterns(self) -> List[RecoveryPattern]:
        return list(self._patterns.values())
