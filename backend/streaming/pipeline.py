"""
Agentic AutoML Intelligence Platform — CDC Streaming Pipeline
Processes Change Data Capture event streams, updates feature store, and triggers real-time inference.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional
from loguru import logger

from streaming.schemas import CDCEvent, CDCEventBatch, CDCOperation, ProcessingStatus
from streaming.idempotency import event_idempotency
from feature_store.store import feature_store


class CDCPipeline:
    """End-to-end Change Data Capture event ingestion pipeline."""

    def __init__(self, prediction_handler: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.prediction_handler = prediction_handler
        self._processed_count: int = 0
        self._duplicate_count: int = 0
        self._error_count: int = 0

    def process_event(self, event: CDCEvent) -> CDCEvent:
        """Process a single CDC event with idempotency, feature store persistence, and inference."""
        # 1. Idempotency Check
        if event_idempotency.is_duplicate(event.event_id):
            logger.debug(f"[CDCPipeline] Duplicate event '{event.event_id}' skipped.")
            event.processing_status = ProcessingStatus.DUPLICATE
            self._duplicate_count += 1
            return event

        try:
            # 2. Extract and Normalize features from payload
            payload = event.payload
            if not isinstance(payload, dict):
                raise ValueError("CDC event payload must be a key-value dictionary.")

            # 3. Write features into Online & Offline Feature Store
            feature_store.write_online_features(
                entity_id=event.entity_id,
                features=payload,
                timestamp=event.timestamp,
            )

            # 4. Optional Real-Time Inference trigger
            if self.prediction_handler and event.operation in (CDCOperation.INSERT, CDCOperation.UPDATE):
                try:
                    self.prediction_handler({"entity_id": event.entity_id, **payload})
                except Exception as pred_err:
                    logger.warning(f"[CDCPipeline] Optional prediction trigger warning: {pred_err}")

            # 5. Mark processed and register idempotency
            event_idempotency.mark_processed(event.event_id)
            event.processing_status = ProcessingStatus.PROCESSED
            self._processed_count += 1
            return event

        except Exception as e:
            logger.error(f"[CDCPipeline] Error processing event '{event.event_id}': {e}")
            event.processing_status = ProcessingStatus.FAILED
            event.error_message = str(e)
            self._error_count += 1
            return event

    def process_batch(self, batch: CDCEventBatch) -> List[CDCEvent]:
        """Process an entire batch of CDC events."""
        results = []
        for evt in batch.events:
            results.append(self.process_event(evt))
        return results

    def get_metrics(self) -> Dict[str, int]:
        return {
            "processed": self._processed_count,
            "duplicates": self._duplicate_count,
            "errors": self._error_count,
        }


cdc_pipeline = CDCPipeline()
