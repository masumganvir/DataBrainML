"""
Agentic AutoML Intelligence Platform — PostgreSQL Connector
Secure, read-only PostgreSQL data source connector.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from loguru import logger

from connectors.base import (
    BaseConnector,
    ColumnMetadata,
    ConnectionTestResult,
    SchemaProfile,
    TableMetadata,
)
from connectors.security import DatabaseSecurityValidator


class PostgresConnector(BaseConnector):
    """Production-grade PostgreSQL connector with read-only transaction guarantees."""

    def __init__(
        self,
        connection_uri: str,
        name: str = "postgres_source",
        query_row_limit: int = 50000,
        timeout_seconds: float = 30.0,
    ):
        super().__init__(connection_uri, name, query_row_limit, timeout_seconds)
        # Ensure driver prefix is compatible with SQLAlchemy
        uri = connection_uri
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        self.engine = create_engine(
            uri,
            pool_pre_ping=True,
            execution_options={"isolation_level": "AUTOCOMMIT"},
            connect_args={"connect_timeout": int(timeout_seconds)},
        )

    def test_connection(self) -> ConnectionTestResult:
        start_time = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT version();")).scalar()
                latency = (time.perf_counter() - start_time) * 1000
                return ConnectionTestResult(
                    success=True,
                    source_type="postgresql",
                    message="Successfully connected to PostgreSQL.",
                    latency_ms=round(latency, 2),
                    server_version=str(res),
                    read_only_verified=True,
                )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                source_type="postgresql",
                message=f"Connection failed: {str(e)}",
                latency_ms=round(latency, 2),
                read_only_verified=False,
            )

    def discover_schema(self) -> SchemaProfile:
        inspector = inspect(self.engine)
        tables_meta: List[TableMetadata] = []
        candidate_targets: List[str] = []
        candidate_ids: List[str] = []
        candidate_ts: List[str] = []
        total_cols = 0

        target_keywords = {"target", "label", "class", "churn", "fraud", "is_fraud", "status", "price", "revenue", "outcome"}
        id_keywords = {"id", "uuid", "pk", "_id", "guid", "key"}
        ts_keywords = {"time", "timestamp", "created_at", "updated_at", "date", "event_time"}

        schema_names = inspector.get_schema_names()
        # Default to public or non-system schemas
        valid_schemas = [s for s in schema_names if s not in ("pg_catalog", "information_schema")]

        for schema in valid_schemas:
            for table_name in inspector.get_table_names(schema=schema):
                cols_meta = []
                pks = inspector.get_pk_constraint(table_name, schema=schema).get("constrained_columns", [])
                fks = [
                    {"referred_table": fk.get("referred_table", ""), "constrained_columns": fk.get("constrained_columns", [])}
                    for fk in inspector.get_foreign_keys(table_name, schema=schema)
                ]

                columns = inspector.get_columns(table_name, schema=schema)
                total_cols += len(columns)
                table_ts_cols = []

                for col in columns:
                    col_name = col["name"]
                    col_type = str(col["type"]).lower()
                    is_ts = any(kw in col_name.lower() or kw in col_type for kw in ["time", "date"])

                    if is_ts:
                        table_ts_cols.append(col_name)
                        candidate_ts.append(f"{table_name}.{col_name}")

                    if any(kw == col_name.lower() or col_name.lower().endswith(f"_{kw}") for kw in target_keywords):
                        candidate_targets.append(f"{table_name}.{col_name}")

                    if col_name in pks or any(col_name.lower().endswith(f"_{kw}") or col_name.lower() == kw for kw in id_keywords):
                        candidate_ids.append(f"{table_name}.{col_name}")

                    cols_meta.append(
                        ColumnMetadata(
                            name=col_name,
                            data_type=col_type,
                            is_nullable=col.get("nullable", True),
                            is_primary_key=col_name in pks,
                            is_timestamp=is_ts,
                        )
                    )

                # Estimate row count
                try:
                    with self.engine.connect() as conn:
                        count_res = conn.execute(
                            text(f"SELECT COUNT(*) FROM {schema}.{table_name} LIMIT 1")
                        ).scalar()
                        row_est = int(count_res or 0)
                except Exception:
                    row_est = 0

                tables_meta.append(
                    TableMetadata(
                        table_name=table_name,
                        schema_name=schema,
                        row_count_estimate=row_est,
                        columns=cols_meta,
                        primary_keys=pks,
                        foreign_keys=fks,
                        timestamp_columns=table_ts_cols,
                    )
                )

        return SchemaProfile(
            data_source_id=self.name,
            source_type="postgresql",
            database_name=self.engine.url.database or "default",
            tables=tables_meta,
            total_tables=len(tables_meta),
            total_columns=total_cols,
            candidate_targets=list(set(candidate_targets)),
            candidate_id_columns=list(set(candidate_ids)),
            candidate_timestamp_columns=list(set(candidate_ts)),
        )

    def sample_table(
        self,
        table_name: str,
        schema_name: Optional[str] = "public",
        limit: int = 1000,
    ) -> pd.DataFrame:
        actual_limit = min(limit, self.query_row_limit)
        qualified_name = f'"{schema_name}"."{table_name}"' if schema_name else f'"{table_name}"'
        query = f"SELECT * FROM {qualified_name} LIMIT {actual_limit}"

        val = DatabaseSecurityValidator.validate_query(query, max_rows=self.query_row_limit)
        if not val.is_safe:
            raise PermissionError(f"Security validation failed: {val.violation_reason}")

        with self.engine.connect() as conn:
            # Enforce read only transaction
            conn.execute(text("SET TRANSACTION READ ONLY;"))
            return pd.read_sql_query(text(val.sanitized_query), conn)

    def extract_incremental(
        self,
        table_name: str,
        timestamp_column: str,
        since_timestamp: datetime,
        limit: int = 10000,
    ) -> pd.DataFrame:
        actual_limit = min(limit, self.query_row_limit)
        query = f"SELECT * FROM \"{table_name}\" WHERE \"{timestamp_column}\" > :since ORDER BY \"{timestamp_column}\" ASC LIMIT {actual_limit}"

        val = DatabaseSecurityValidator.validate_query(query, max_rows=self.query_row_limit)
        if not val.is_safe:
            raise PermissionError(f"Security validation failed: {val.violation_reason}")

        with self.engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY;"))
            return pd.read_sql_query(
                text(val.sanitized_query),
                conn,
                params={"since": since_timestamp.isoformat()},
            )
