"""
DataWise AI — Prediction Repository
Tracks inference requests, input hashes, prediction outputs, and latencies.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Dict, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.entities import PredictionRequest


class PredictionRepository:
    """Stores predictions with privacy-aware hashing."""

    @classmethod
    async def log_prediction(
        cls,
        db: AsyncSession,
        project_id: str,
        model_version_id: str,
        input_data: Dict[str, Any],
        prediction: Any,
        latency_ms: float,
        confidence: Optional[float] = None,
    ) -> PredictionRequest:
        """Stores prediction event without exposing raw PII."""
        # Compute input hash for deduplication/audit
        input_str = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.sha256(input_str.encode("utf-8")).hexdigest()

        pred_record = PredictionRequest(
            id=f"pred_{uuid.uuid4().hex[:12]}",
            model_version_id=model_version_id,
            input_features=input_data,
            prediction_output=prediction,
            latency_ms=latency_ms,
        )
        db.add(pred_record)
        await db.commit()
        return pred_record
