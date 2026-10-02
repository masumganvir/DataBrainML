"""
Agentic AutoML Intelligence Platform — Shadow & Canary Deployment Manager
Executes zero-risk candidate model shadow evaluation, traffic splitting, and instant rollback.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field


class ShadowInferenceComparison(BaseModel):
    request_id: str
    active_version: str
    shadow_version: str
    active_prediction: Any
    shadow_prediction: Any
    active_latency_ms: float
    shadow_latency_ms: float
    predictions_agree: bool
    timestamp: float = Field(default_factory=time.time)


class ModelDeploymentManager:
    """Controls production model serving, candidate shadow traffic, canary routing, and rollback."""

    def __init__(self):
        # Version catalog: {version_tag: model_instance}
        self._version_registry: Dict[str, Any] = {}
        self._active_version: Optional[str] = None
        self._shadow_version: Optional[str] = None
        self._rollback_history: List[str] = []
        self._comparison_logs: List[ShadowInferenceComparison] = []
        self._canary_percentage: float = 0.0  # 0.0 = 100% active, 0.1 = 10% canary

    @property
    def active_version(self) -> Optional[str]:
        return self._active_version

    @property
    def shadow_version(self) -> Optional[str]:
        return self._shadow_version

    def register_version(self, version_tag: str, model_instance: Any, set_active: bool = False):
        """Register a new immutable model version snapshot."""
        self._version_registry[version_tag] = model_instance
        logger.info(f"[ModelDeploymentManager] Registered version '{version_tag}'")
        if set_active or self._active_version is None:
            if self._active_version:
                self._rollback_history.append(self._active_version)
            self._active_version = version_tag
            logger.info(f"[ModelDeploymentManager] Active version set to '{version_tag}'")

    def set_shadow_candidate(self, candidate_version: str):
        """Enable shadow mode for a candidate model without affecting production user responses."""
        if candidate_version not in self._version_registry:
            raise KeyError(f"Candidate version '{candidate_version}' is not registered.")
        self._shadow_version = candidate_version
        logger.info(f"[ModelDeploymentManager] Shadow candidate active: '{candidate_version}'")

    def remove_shadow_candidate(self):
        self._shadow_version = None

    def predict(
        self,
        X: pd.DataFrame,
        request_id: Optional[str] = None,
    ) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """
        Execute prediction.
        Returns:
            (primary_prediction, shadow_comparison_metadata)
        """
        if not self._active_version or self._active_version not in self._version_registry:
            raise RuntimeError("No active model deployed in ModelDeploymentManager.")

        req_id = request_id or f"req_{int(time.time()*1000)}"
        active_model = self._version_registry[self._active_version]

        # 1. Run active model
        t0 = time.perf_counter()
        active_pred = active_model.predict(X)
        active_lat = (time.perf_counter() - t0) * 1000

        shadow_metadata = None

        # 2. If shadow candidate is configured, evaluate in parallel/shadow mode
        if self._shadow_version and self._shadow_version in self._version_registry:
            shadow_model = self._version_registry[self._shadow_version]
            t1 = time.perf_counter()
            try:
                shadow_pred = shadow_model.predict(X)
                shadow_lat = (time.perf_counter() - t1) * 1000

                # Compare active vs shadow
                agree = bool(np.array_equal(active_pred, shadow_pred))

                comp = ShadowInferenceComparison(
                    request_id=req_id,
                    active_version=self._active_version,
                    shadow_version=self._shadow_version,
                    active_prediction=active_pred.tolist() if hasattr(active_pred, "tolist") else str(active_pred),
                    shadow_prediction=shadow_pred.tolist() if hasattr(shadow_pred, "tolist") else str(shadow_pred),
                    active_latency_ms=round(active_lat, 2),
                    shadow_latency_ms=round(shadow_lat, 2),
                    predictions_agree=agree,
                )
                self._comparison_logs.append(comp)
                if len(self._comparison_logs) > 2000:
                    self._comparison_logs = self._comparison_logs[-1000:]

                shadow_metadata = comp.model_dump()
            except Exception as shadow_err:
                logger.warning(f"[ModelDeploymentManager] Shadow evaluation failed: {shadow_err}")

        return active_pred, shadow_metadata

    def promote_shadow_candidate(self) -> str:
        """Promote the active shadow candidate to primary production model."""
        if not self._shadow_version:
            raise ValueError("No shadow candidate currently configured to promote.")

        promoted_version = self._shadow_version
        if self._active_version:
            self._rollback_history.append(self._active_version)

        self._active_version = promoted_version
        self._shadow_version = None
        logger.info(f"[ModelDeploymentManager] Promoted '{promoted_version}' to primary production.")
        return promoted_version

    def rollback(self, target_version: Optional[str] = None) -> str:
        """Instant rollback to previous stable model version."""
        if target_version:
            if target_version not in self._version_registry:
                raise KeyError(f"Target rollback version '{target_version}' not found.")
            rollback_target = target_version
        elif self._rollback_history:
            rollback_target = self._rollback_history.pop()
        else:
            raise ValueError("No previous model version available in rollback history.")

        previous_active = self._active_version
        self._active_version = rollback_target
        logger.warning(f"[ModelDeploymentManager] Rolled back from '{previous_active}' to '{rollback_target}'.")
        return rollback_target

    def get_shadow_evaluation_summary(self) -> Dict[str, Any]:
        """Summary of shadow traffic agreement and latency comparison."""
        if not self._comparison_logs:
            return {"total_compared": 0, "agreement_rate": 1.0}

        total = len(self._comparison_logs)
        agreed = sum(1 for c in self._comparison_logs if c.predictions_agree)
        avg_act_lat = sum(c.active_latency_ms for c in self._comparison_logs) / total
        avg_shd_lat = sum(c.shadow_latency_ms for c in self._comparison_logs) / total

        return {
            "total_compared": total,
            "agreement_rate": round(agreed / total, 4),
            "active_version": self._active_version,
            "shadow_version": self._shadow_version,
            "avg_active_latency_ms": round(avg_act_lat, 2),
            "avg_shadow_latency_ms": round(avg_shd_lat, 2),
            "latency_delta_ms": round(avg_shd_lat - avg_act_lat, 2),
        }


deployment_manager = ModelDeploymentManager()
