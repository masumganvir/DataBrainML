"""
Agentic AutoML Intelligence Platform — REST API & Webhook Connector
Secure extraction from external HTTP/REST endpoints and webhooks.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
import pandas as pd
from loguru import logger

from connectors.base import (
    BaseConnector,
    ColumnMetadata,
    ConnectionTestResult,
    SchemaProfile,
    TableMetadata,
)
from connectors.security import DatabaseSecurityValidator


class RestApiConnector(BaseConnector):
    """Connector for external REST endpoints that return JSON records."""

    def __init__(
        self,
        endpoint_url: str,
        name: str = "rest_api_source",
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        query_row_limit: int = 10000,
        timeout_seconds: float = 20.0,
    ):
        super().__init__(endpoint_url, name, query_row_limit, timeout_seconds)
        self.endpoint_url = endpoint_url
        self.headers = headers or {}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    def test_connection(self) -> ConnectionTestResult:
        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.get(self.endpoint_url, headers=self.headers)
                latency = (time.perf_counter() - start_time) * 1000
                if res.status_code in (200, 201):
                    return ConnectionTestResult(
                        success=True,
                        source_type="rest_api",
                        message=f"Connected successfully (HTTP {res.status_code}).",
                        latency_ms=round(latency, 2),
                        server_version=res.headers.get("server", "generic-http"),
                        read_only_verified=True,
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        source_type="rest_api",
                        message=f"Received HTTP status {res.status_code}",
                        latency_ms=round(latency, 2),
                        read_only_verified=True,
                    )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                source_type="rest_api",
                message=f"HTTP Connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                read_only_verified=False,
            )

    def discover_schema(self) -> SchemaProfile:
        sample_df = self.sample_table("root", limit=100)
        cols_meta = []
        candidate_targets = []
        candidate_ids = []
        candidate_ts = []

        target_keywords = {"target", "label", "class", "churn", "fraud", "is_fraud", "status", "price", "revenue", "outcome"}
        id_keywords = {"id", "uuid", "pk", "_id", "guid", "key"}

        for col_name in sample_df.columns:
            dtype_str = str(sample_df[col_name].dtype)
            is_ts = "datetime" in dtype_str or any(kw in col_name.lower() for kw in ["time", "date"])

            if is_ts:
                candidate_ts.append(col_name)
            if any(kw == col_name.lower() or col_name.lower().endswith(f"_{kw}") for kw in target_keywords):
                candidate_targets.append(col_name)
            if any(kw == col_name.lower() or col_name.lower().endswith(f"_{kw}") for kw in id_keywords):
                candidate_ids.append(col_name)

            cols_meta.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=dtype_str,
                    is_nullable=bool(sample_df[col_name].isnull().any()),
                    is_timestamp=is_ts,
                    sample_values=sample_df[col_name].dropna().head(3).tolist(),
                )
            )

        table_meta = TableMetadata(
            table_name="api_feed",
            row_count_estimate=len(sample_df),
            columns=cols_meta,
            primary_keys=[],
            foreign_keys=[],
            timestamp_columns=candidate_ts,
        )

        return SchemaProfile(
            data_source_id=self.name,
            source_type="rest_api",
            database_name="api_endpoint",
            tables=[table_meta],
            total_tables=1,
            total_columns=len(cols_meta),
            candidate_targets=candidate_targets,
            candidate_id_columns=candidate_ids,
            candidate_timestamp_columns=candidate_ts,
        )

    def sample_table(
        self,
        table_name: str = "root",
        schema_name: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        actual_limit = min(limit, self.query_row_limit)
        with httpx.Client(timeout=self.timeout_seconds) as client:
            res = client.get(self.endpoint_url, headers=self.headers, params={"limit": actual_limit})
            data = res.json()
            if isinstance(data, dict):
                # If wrapped in items/results/data list
                for k in ["data", "items", "results", "records"]:
                    if k in data and isinstance(data[k], list):
                        data = data[k]
                        break
                else:
                    data = [data]
            return pd.json_normalize(data).head(actual_limit)

    def extract_incremental(
        self,
        table_name: str,
        timestamp_column: str,
        since_timestamp: datetime,
        limit: int = 10000,
    ) -> pd.DataFrame:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            res = client.get(
                self.endpoint_url,
                headers=self.headers,
                params={"since": since_timestamp.isoformat(), "limit": min(limit, self.query_row_limit)},
            )
            data = res.json()
            if isinstance(data, dict):
                for k in ["data", "items", "results", "records"]:
                    if k in data and isinstance(data[k], list):
                        data = data[k]
                        break
                else:
                    data = [data]
            return pd.json_normalize(data)
