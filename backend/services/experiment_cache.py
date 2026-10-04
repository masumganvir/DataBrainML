"""
DataWise AI — Experiment Cache & Deduplication
Implements Prompt Section 23 & 29:
- Computes deterministic fingerprint:
    SHA256(dataset_hash + pipeline_config + model_config + training_config)
- Detects if an identical experiment has already been trained
- Prevents redundant training compute
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional
from loguru import logger


class ExperimentCache:
    """Computes experiment fingerprints and tracks historical runs."""

    @staticmethod
    def generate_fingerprint(
        dataset_hash: str,
        pipeline_config: Dict[str, Any],
        model_name: str,
        hyperparameters: Dict[str, Any],
        training_config: Dict[str, Any],
    ) -> str:
        """
        Calculates cryptographic SHA-256 fingerprint of the experiment specification.
        Identical inputs guarantee identical hashes.
        """
        payload = {
            "dataset_hash": dataset_hash,
            "pipeline_config": pipeline_config,
            "model_name": model_name,
            "hyperparameters": hyperparameters,
            "training_config": training_config,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def check_cache(fingerprint: str) -> Optional[Dict[str, Any]]:
        """Checks if identical model was already computed (in-memory/DB)."""
        # In-memory fast cache
        return _EXPERIMENT_CACHE_STORE.get(fingerprint)

    @staticmethod
    def record_cache(fingerprint: str, run_id: str, model_name: str, score: float) -> None:
        """Records completed experiment in cache."""
        _EXPERIMENT_CACHE_STORE[fingerprint] = {
            "fingerprint": fingerprint,
            "run_id": run_id,
            "model_name": model_name,
            "primary_score": score,
        }


_EXPERIMENT_CACHE_STORE: Dict[str, Dict[str, Any]] = {}
experiment_cache = ExperimentCache()
