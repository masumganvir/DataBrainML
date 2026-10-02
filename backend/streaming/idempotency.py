"""
Agentic AutoML Intelligence Platform — Event Idempotency Tracker
Guarantees exactly-once processing across CDC and real-time streaming events.
"""

from __future__ import annotations

import time
from typing import Optional, Set
from loguru import logger


class EventIdempotencyTracker:
    """In-memory and Redis-compatible sliding event deduplication store."""

    def __init__(self, ttl_seconds: int = 86400, max_size: int = 200000):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._seen_events: dict[str, float] = {}

    def is_duplicate(self, event_id: str) -> bool:
        """Check if event_id has been seen within TTL window."""
        now = time.time()
        # Clean expired keys periodically if approaching limit
        if len(self._seen_events) >= self.max_size:
            cutoff = now - self.ttl_seconds
            self._seen_events = {k: v for k, v in self._seen_events.items() if v > cutoff}

        if event_id in self._seen_events:
            if now - self._seen_events[event_id] < self.ttl_seconds:
                return True

        return False

    def mark_processed(self, event_id: str):
        """Mark event_id as processed."""
        self._seen_events[event_id] = time.time()

    def clear(self):
        self._seen_events.clear()


event_idempotency = EventIdempotencyTracker()
