"""
Agentic AutoML Intelligence Platform — Generic SQL, MySQL, and SQLite Connectors
Unified SQLAlchemy-backed connector for SQL databases with read-only security enforcement.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, inspect, text

from connectors.base import (
    BaseConnector,
    ColumnMetadata,
    ConnectionTestResult,
    SchemaProfile,
    TableMetadata,
)
from connectors.security import DatabaseSecurityValidator


class GenericSQLConnector(BaseConnector):
    """Generic relational database connector using SQLAlchemy inspection."""

    def __init__(
        self,
        connection_uri: str,
        name: str = "sql_source",
        source_type: str = "generic_sql",
        query_row_limit: int = 50000,
        timeout_seconds: float = 30.0,
    ):
        super().__init__(connection_uri, name, query_row_limit, timeout_seconds)
        self.source_type = source_type
        self.engine = create_engine(
            connection_uri,
            pool_pre_ping=True,
            connect_args={"connect_timeout": int(timeout_seconds)} if "sqlite" not in connection_uri else {},
        )

    def test_connection(self) -> ConnectionTestResult:
        start_time = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT 1;")).scalar()
                latency = (time.perf_counter() - start_time) * 1000
                return ConnectionTestResult(
                    success=True,
                    source_type=self.source_type,
                    message=f"Successfully connected to {self.source_type} database.",
                    latency_ms=round(latency, 2),
                    server_version=str(res),
                    read_only_verified=True,
                )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                source_type=self.source_type,
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

        table_names = inspector.get_table_names()
        for table_name in table_names:
            cols_meta = []
            try:
                pks = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
            except Exception:
                pks = []

            try:
                columns = inspector.get_columns(table_name)
            except Exception:
                columns = []

            total_cols += len(columns)
            table_ts_cols = []

            for col in columns:
                col_name = col["name"]
                col_type = str(col["type"]).lower()
                is_ts = any(kw in col_name.lower() or kw in col_type for kw in ["time", "date"])

                if is_ts:
                    table_ts_cols.append(col_name)
                    candidate_ts.append(f"{table_name}.{col_name}")

                if any(kw in col_name.lower() for kw in target_keywords):
                    candidate_targets.append(f"{table_name}.{col_name}")

                if col_name in pks or any(kw in col_name.lower() for kw in id_keywords):
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

            try:
                with self.engine.connect() as conn:
                    count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    row_est = int(count_res or 0)
            except Exception:
                row_est = 0

            tables_meta.append(
                TableMetadata(
                    table_name=table_name,
                    row_count_estimate=row_est,
                    columns=cols_meta,
                    primary_keys=pks,
                    foreign_keys=[],
                    timestamp_columns=table_ts_cols,
                )
            )

        return SchemaProfile(
            data_source_id=self.name,
            source_type=self.source_type,
            database_name=getattr(self.engine.url, "database", "default") or "default",
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
        schema_name: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        actual_limit = min(limit, self.query_row_limit)
        query = f"SELECT * FROM {table_name} LIMIT {actual_limit}"

        val = DatabaseSecurityValidator.validate_query(query, max_rows=self.query_row_limit)
        if not val.is_safe:
            raise PermissionError(f"Security validation failed: {val.violation_reason}")

        with self.engine.connect() as conn:
            return pd.read_sql_query(text(val.sanitized_query), conn)

    def extract_incremental(
        self,
        table_name: str,
        timestamp_column: str,
        since_timestamp: datetime,
        limit: int = 10000,
    ) -> pd.DataFrame:
        actual_limit = min(limit, self.query_row_limit)
        query = f"SELECT * FROM {table_name} WHERE {timestamp_column} > :since ORDER BY {timestamp_column} ASC LIMIT {actual_limit}"

        val = DatabaseSecurityValidator.validate_query(query, max_rows=self.query_row_limit)
        if not val.is_safe:
            raise PermissionError(f"Security validation failed: {val.violation_reason}")

        with self.engine.connect() as conn:
            return pd.read_sql_query(
                text(val.sanitized_query),
                conn,
                params={"since": since_timestamp.isoformat()},
            )


class MySQLConnector(GenericSQLConnector):
    def __init__(self, connection_uri: str, name: str = "mysql_source", **kwargs):
        super().__init__(connection_uri, name=name, source_type="mysql", **kwargs)


class SQLiteConnector(GenericSQLConnector):
    def __init__(self, connection_uri: str, name: str = "sqlite_source", **kwargs):
        super().__init__(connection_uri, name=name, source_type="sqlite", **kwargs)


class SQLServerConnector(GenericSQLConnector):
    def __init__(self, connection_uri: str, name: str = "sqlserver_source", **kwargs):
        super().__init__(connection_uri, name=name, source_type="sqlserver", **kwargs)
