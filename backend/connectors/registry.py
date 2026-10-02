"""
Agentic AutoML Intelligence Platform — Connector Registry
Factory and lifecycle manager for all data connectors.
"""

from __future__ import annotations

from typing import Dict, Type
from connectors.base import BaseConnector
from connectors.postgres import PostgresConnector
from connectors.generic_sql import MySQLConnector, SQLiteConnector, SQLServerConnector, GenericSQLConnector
from connectors.cloud_warehouses import SnowflakeConnector, BigQueryConnector, MongoConnector
from connectors.rest_api import RestApiConnector


class ConnectorRegistry:
    """Manages active connector factories and instantiation."""

    _registry: Dict[str, Type[BaseConnector]] = {
        "postgresql": PostgresConnector,
        "postgres": PostgresConnector,
        "mysql": MySQLConnector,
        "sqlite": SQLiteConnector,
        "sqlserver": SQLServerConnector,
        "mssql": SQLServerConnector,
        "snowflake": SnowflakeConnector,
        "bigquery": BigQueryConnector,
        "mongodb": MongoConnector,
        "mongo": MongoConnector,
        "rest_api": RestApiConnector,
        "webhook": RestApiConnector,
    }

    @classmethod
    def get_connector(
        cls,
        source_type: str,
        connection_uri: str,
        name: str = "source",
        **kwargs,
    ) -> BaseConnector:
        st_lower = source_type.lower()
        connector_cls = cls._registry.get(st_lower)
        if not connector_cls:
            raise ValueError(f"Unsupported connector type: '{source_type}'. Supported: {list(cls._registry.keys())}")
        return connector_cls(connection_uri=connection_uri, name=name, **kwargs)

    @classmethod
    def list_supported_sources(cls) -> list[str]:
        return sorted(list(cls._registry.keys()))
