"""
Rollback Manager & Checkpoint Recovery
Manages stage-level checkpoint snapshots across LangGraph workflows,
enabling targeted resumes from nearest safe checkpoints without restarts.
"""

from __future__ import annotations

import copy
import time
from typing import Any, Dict, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

# Standard LangGraph Stages mapped to checkpoints
CHECKPOINT_STAGES: List[str] = [
    "checkpoint_1_data_loaded",
    "checkpoint_2_profile_complete",
    "checkpoint_3_eda_complete",
    "checkpoint_4_preprocessing_complete",
    "checkpoint_5_feature_engineering_complete",
    "checkpoint_6_baseline_complete",
    "checkpoint_7_optimization_complete",
    "checkpoint_8_final_model_validated",
    "checkpoint_9_deployment_validated",
]

STAGE_TO_CHECKPOINT: Dict[str, str] = {
    "data_ingestion": "checkpoint_1_data_loaded",
    "data_profiling": "checkpoint_2_profile_complete",
    "eda": "checkpoint_3_eda_complete",
    "preprocessing": "checkpoint_4_preprocessing_complete",
    "feature_engineering": "checkpoint_5_feature_engineering_complete",
    "baseline_training": "checkpoint_6_baseline_complete",
    "optimization": "checkpoint_7_optimization_complete",
    "evaluation": "checkpoint_8_final_model_validated",
    "deployment": "checkpoint_9_deployment_validated",
}


class CheckpointSnapshot(BaseModel):
    checkpoint_id: str
    stage_name: str
    workflow_id: str
    timestamp: float = Field(default_factory=time.time)
    state_payload: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""

    class Config:
        arbitrary_types_allowed = True


class RollbackManager:
    """Stores and retrieves checkpoint state snapshots for safe rollback and resume."""

    def __init__(self):
        # workflow_id -> list of CheckpointSnapshots
        self._checkpoints: Dict[str, List[CheckpointSnapshot]] = {}

    def save_checkpoint(
        self,
        workflow_id: str,
        stage_name: str,
        state_data: Dict[str, Any],
        summary: str = "",
    ) -> CheckpointSnapshot:
        """Records a safe checkpoint snapshot for a workflow stage."""
        cp_id = STAGE_TO_CHECKPOINT.get(stage_name, f"checkpoint_{stage_name}")

        # Filter out unpickleable or large raw streams, preserving metadata
        clean_state = {}
        for k, v in state_data.items():
            if k in ("db", "session", "connection", "lock"):
                continue
            clean_state[k] = v

        snapshot = CheckpointSnapshot(
            checkpoint_id=cp_id,
            stage_name=stage_name,
            workflow_id=workflow_id,
            state_payload=clean_state,
            summary=summary or f"Completed {stage_name}",
        )

        if workflow_id not in self._checkpoints:
            self._checkpoints[workflow_id] = []

        # Remove duplicate checkpoint for same stage if already recorded
        self._checkpoints[workflow_id] = [
            cp for cp in self._checkpoints[workflow_id] if cp.checkpoint_id != cp_id
        ]
        self._checkpoints[workflow_id].append(snapshot)
        logger.info(f"Recorded checkpoint {cp_id} for workflow {workflow_id}")
        return snapshot

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[CheckpointSnapshot]:
        """Returns the most recent checkpoint for a workflow."""
        snapshots = self._checkpoints.get(workflow_id, [])
        return snapshots[-1] if snapshots else None

    def get_nearest_safe_checkpoint(
        self, workflow_id: str, failed_stage: str
    ) -> Optional[CheckpointSnapshot]:
        """
        Locates the safe checkpoint immediately prior to the failed stage.
        E.g., if stage 8 fails, resumes from checkpoint 7.
        """
        snapshots = self._checkpoints.get(workflow_id, [])
        if not snapshots:
            return None

        failed_cp = STAGE_TO_CHECKPOINT.get(failed_stage, "")
        # Find index of failed checkpoint in our standard progression
        failed_idx = -1
        for i, cp_name in enumerate(CHECKPOINT_STAGES):
            if cp_name == failed_cp:
                failed_idx = i
                break

        if failed_idx > 0:
            # Look backwards for the most recent valid checkpoint prior to failed_idx
            for prior_cp_name in reversed(CHECKPOINT_STAGES[:failed_idx]):
                for snap in snapshots:
                    if snap.checkpoint_id == prior_cp_name:
                        logger.info(f"Rollback targets prior checkpoint: {snap.checkpoint_id}")
                        return snap

        # Fallback to the latest recorded checkpoint
        return snapshots[-1]

    def clear(self, workflow_id: str) -> None:
        self._checkpoints.pop(workflow_id, None)
