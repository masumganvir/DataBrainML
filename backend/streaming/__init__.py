"""
Agentic AutoML Intelligence Platform — Streaming & CDC Package
"""

from streaming.schemas import (
    CDCEvent,
    CDCEventBatch,
    CDCOperation,
    ProcessingStatus,
)
from streaming.idempotency import EventIdempotencyTracker, event_idempotency
from streaming.pipeline import CDCPipeline, cdc_pipeline

__all__ = [
    "CDCEvent",
    "CDCEventBatch",
    "CDCOperation",
    "ProcessingStatus",
    "EventIdempotencyTracker",
    "event_idempotency",
    "CDCPipeline",
    "cdc_pipeline",
]
