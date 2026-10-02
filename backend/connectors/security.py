"""
Agentic AutoML Intelligence Platform — Database Security Validator
Enforces zero-trust database security, query sanitization, and read-only constraints.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set
from pydantic import BaseModel, Field


class SecurityValidationResult(BaseModel):
    is_safe: bool
    violation_reason: Optional[str] = None
    sanitized_query: Optional[str] = None
    blocked_keywords: List[str] = Field(default_factory=list)


class DatabaseSecurityValidator:
    """Enforces strict read-only execution boundaries on external databases."""

    # Explicit list of forbidden destructive keywords and SQL statements
    FORBIDDEN_KEYWORDS: Set[str] = {
        "DROP",
        "TRUNCATE",
        "DELETE",
        "ALTER",
        "UPDATE",
        "INSERT",
        "GRANT",
        "REVOKE",
        "CREATE",
        "REPLACE",
        "EXEC",
        "EXECUTE",
        "MERGE",
        "UPSERT",
        "CALL",
        "SHUTDOWN",
        "LOCK",
    }

    # Cloud metadata endpoints to prevent SSRF
    BLOCKED_HOSTS: Set[str] = {
        "169.254.169.254",   # AWS/GCP/Azure instance metadata
        "metadata.google.internal",
        "169.254.170.2",     # AWS ECS container credentials
    }

    @classmethod
    def validate_query(
        cls,
        query: str,
        max_rows: int = 50000,
        allowed_tables: Optional[Set[str]] = None,
    ) -> SecurityValidationResult:
        """Validate that a SQL query is strictly read-only and safe to execute."""
        if not query or not query.strip():
            return SecurityValidationResult(
                is_safe=False,
                violation_reason="Query is empty.",
            )

        cleaned_query = query.strip()
        # Remove SQL comments
        cleaned_no_comments = re.sub(r"--.*?$|/\*.*?\*/", "", cleaned_query, flags=re.MULTILINE | re.DOTALL).strip()
        upper_query = cleaned_no_comments.upper()

        # Check for multiple statements (semicolon chaining)
        statements = [s.strip() for s in cleaned_no_comments.split(";") if s.strip()]
        if len(statements) > 1:
            return SecurityValidationResult(
                is_safe=False,
                violation_reason="Multiple statements (query chaining) are strictly prohibited.",
            )

        # Check for forbidden keywords as standalone word tokens first
        found_forbidden = []
        for kw in cls.FORBIDDEN_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", upper_query):
                found_forbidden.append(kw)

        if found_forbidden:
            return SecurityValidationResult(
                is_safe=False,
                violation_reason=f"Forbidden destructive operations detected: {', '.join(found_forbidden)}",
                blocked_keywords=found_forbidden,
            )

        # Must start with SELECT or WITH (for CTEs) or EXPLAIN
        if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", upper_query):
            return SecurityValidationResult(
                is_safe=False,
                violation_reason="Only SELECT or read-only WITH queries are permitted.",
            )

        # Inject LIMIT if not already present or higher than max_rows
        limit_match = re.search(r"\bLIMIT\s+(\d+)", upper_query)
        if not limit_match:
            sanitized = f"{cleaned_no_comments} LIMIT {max_rows}"
        else:
            current_limit = int(limit_match.group(1))
            if current_limit > max_rows:
                sanitized = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {max_rows}", cleaned_no_comments, flags=re.IGNORECASE)
            else:
                sanitized = cleaned_no_comments

        return SecurityValidationResult(
            is_safe=True,
            sanitized_query=sanitized,
        )

    @classmethod
    def validate_connection_target(cls, host: str, port: int) -> bool:
        """Prevent SSRF attacks to internal cloud infrastructure."""
        h_lower = host.lower()
        if h_lower in cls.BLOCKED_HOSTS:
            return False
        return True
