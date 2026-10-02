"""
Agentic AutoML Intelligence Platform — Database Connector Base Specification
Enterprise read-only database and external stream connector interface.
"""

from __future__ import annotations

import abc
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_timestamp: bool = False
    sample_values: List[Any] = Field(default_factory=list)
    distinct_count_estimate: Optional[int] = None


class TableMetadata(BaseModel):
    table_name: str
    schema_name: Optional[str] = None
    row_count_estimate: int = 0
    columns: List[ColumnMetadata] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = Field(default_factory=list)
    timestamp_columns: List[str] = Field(default_factory=list)


class SchemaProfile(BaseModel):
    data_source_id: str
    source_type: str
    database_name: str
    tables: List[TableMetadata] = Field(default_factory=list)
    total_tables: int = 0
    total_columns: int = 0
    candidate_targets: List[str] = Field(default_factory=list)
    candidate_id_columns: List[str] = Field(default_factory=list)
    candidate_timestamp_columns: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConnectionTestResult(BaseModel):
    success: bool
    source_type: str
    message: str
    latency_ms: float
    server_version: Optional[str] = None
    read_only_verified: bool = True


class BaseConnector(abc.ABC):
    """Abstract base class for all enterprise data source connectors."""

    def __init__(
        self,
        connection_uri: str,
        name: str = "default_source",
        query_row_limit: int = 50000,
        timeout_seconds: float = 30.0,
    ):
        self.connection_uri = connection_uri
        self.name = name
        self.query_row_limit = query_row_limit
        self.timeout_seconds = timeout_seconds

    @abc.abstractmethod
    def test_connection(self) -> ConnectionTestResult:
        """Validate credentials, TLS, and read-only access."""
        pass

    @abc.abstractmethod
    def discover_schema(self) -> SchemaProfile:
        """Introspect tables, columns, constraints, and candidate targets."""
        pass

    @abc.abstractmethod
    def sample_table(
        self,
        table_name: str,
        schema_name: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Extract a leakage-safe read-only sample for profiling & EDA."""
        pass

    @abc.abstractmethod
    def extract_incremental(
        self,
        table_name: str,
        timestamp_column: str,
        since_timestamp: datetime,
        limit: int = 10000,
    ) -> pd.DataFrame:
        """Incremental polling for newly modified/inserted records (CDC fallback)."""
        pass
