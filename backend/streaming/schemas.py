"""
Agentic AutoML Intelligence Platform — Streaming & CDC Schemas
Change Data Capture event contracts with strict metadata tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CDCOperation(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SNAPSHOT = "SNAPSHOT"


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    DUPLICATE = "DUPLICATE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    FAILED = "FAILED"


class CDCEvent(BaseModel):
    """Immutable Change Data Capture event representation."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str                                     # e.g., postgres.public.transactions
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    entity_id: str                                  # Primary identifier, e.g., customer_123 or order_456
    operation: CDCOperation = CDCOperation.INSERT
    payload: Dict[str, Any]                         # Changed column dictionary
    schema_version: str = "1.0.0"
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None


class CDCEventBatch(BaseModel):
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    events: List[CDCEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
