"""
Agentic AutoML Intelligence Platform — Feature Store Schemas
Specification for online and offline feature definitions, freshness, and lineage.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureStatus(str, Enum):
    ACTIVE = "active"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class FeatureDefinition(BaseModel):
    """Specification of an enterprise feature as required by Section 17."""
    feature_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_name: str                                # e.g. transaction_count_24h
    entity_key: str = "entity_id"                   # e.g. customer_id, user_id
    description: str = ""
    data_type: str = "float64"                       # int, float, string, boolean
    source: str = "stream"                           # batch, stream, database
    transformation: str = "identity"                 # rolling_count, log1p, mean_7d
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    freshness_sla_seconds: int = 3600                # SLA for feature staleness
    owner: str = "automl_system"
    status: FeatureStatus = FeatureStatus.ACTIVE
    statistics: Dict[str, float] = Field(default_factory=dict) # min, max, mean, std


class EntityFeatures(BaseModel):
    """Online feature vector for a specific entity."""
    entity_id: str
    feature_values: Dict[str, Any]                   # {feature_name: value}
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0.0"


class FeatureStoreQuery(BaseModel):
    entity_ids: List[str]
    feature_names: List[str]
