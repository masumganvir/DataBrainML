"""
Agentic AutoML Intelligence Platform — Database Connectors Package
"""

from connectors.base import (
    BaseConnector,
    ColumnMetadata,
    ConnectionTestResult,
    SchemaProfile,
    TableMetadata,
)
from connectors.security import DatabaseSecurityValidator, SecurityValidationResult
from connectors.postgres import PostgresConnector
from connectors.generic_sql import GenericSQLConnector, MySQLConnector, SQLiteConnector, SQLServerConnector
from connectors.cloud_warehouses import SnowflakeConnector, BigQueryConnector, MongoConnector
from connectors.rest_api import RestApiConnector
from connectors.registry import ConnectorRegistry

__all__ = [
    "BaseConnector",
    "ColumnMetadata",
    "ConnectionTestResult",
    "SchemaProfile",
    "TableMetadata",
    "DatabaseSecurityValidator",
    "SecurityValidationResult",
    "PostgresConnector",
    "GenericSQLConnector",
    "MySQLConnector",
    "SQLiteConnector",
    "SQLServerConnector",
    "SnowflakeConnector",
    "BigQueryConnector",
    "MongoConnector",
    "RestApiConnector",
    "ConnectorRegistry",
]
