"""
PII Redactor
Detects and redacts personally identifiable information (PII) including emails,
phone numbers, SSNs, credit cards, IP addresses, and customer row-level identities.
"""

from __future__ import annotations

import re
from typing import Any, List, Tuple

PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # Email
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")),
    # Phone Numbers (International & Domestic)
    ("phone", re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    # Social Security / National IDs (XXX-XX-XXXX)
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # Credit Card Numbers (13-19 digits with optional hyphens/spaces)
    ("credit_card", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b")),
    # IPv4 / IPv6 addresses
    ("ipv4", re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")),
    ("ipv6", re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")),
    # Specific record/identity leak patterns (e.g. "Row 47291 belonging to John Doe failed because...")
    (
        "record_user_leak",
        re.compile(r"(?i)\brow\s+\d+\s+belonging\s+to\s+([A-Za-z\s]+)\s+failed", re.IGNORECASE)
    ),
    (
        "user_id_row_leak",
        re.compile(r"(?i)(?:user|customer|patient|client)\s+['\"]?([A-Za-z0-9_\-]+)['\"]?\s+(?:record|row)\s+\d+", re.IGNORECASE)
    ),
]


class PIIRedactor:
    """Detects and redacts Personally Identifiable Information (PII)."""

    PII_SUBSTITUTE: str = "[PII_REDACTED]"

    @classmethod
    def detect_pii(cls, text: str) -> bool:
        if not text or not isinstance(text, str):
            return False
        for _, pattern in PII_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def redact_pii(cls, text: str) -> str:
        if not text or not isinstance(text, str):
            return text

        sanitized = text

        # Specific replacement for row/record identity leaks
        sanitized = re.sub(
            r"(?i)\brow\s+\d+\s+belonging\s+to\s+[A-Za-z\s]+\s+failed\s+because",
            "One record failed validation because",
            sanitized,
        )

        for name, pattern in PII_PATTERNS:
            if name == "record_user_leak":
                continue
            sanitized = pattern.sub(f"[{name.upper()}_REDACTED]", sanitized)

        return sanitized

    @classmethod
    def sanitize_recursive(cls, data: Any) -> Any:
        if isinstance(data, str):
            return cls.redact_pii(data)
        elif isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                lower_k = str(k).lower()
                if any(pii_term in lower_k for pii_term in ["email", "phone", "ssn", "credit_card", "first_name", "last_name", "full_name", "national_id"]):
                    clean[k] = cls.PII_SUBSTITUTE
                else:
                    clean[k] = cls.sanitize_recursive(v)
            return clean
        elif isinstance(data, list):
            return [cls.sanitize_recursive(item) for item in data]
        return data


def redact_pii(text: str) -> str:
    return PIIRedactor.redact_pii(text)


def detect_pii(text: str) -> bool:
    return PIIRedactor.detect_pii(text)
