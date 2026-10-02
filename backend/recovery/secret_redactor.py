"""
Secret Redactor
Enforces zero secret leakage across logs, error objects, reports, notebooks, and user-facing messages.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Union

SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # API Keys: Gemini, Groq, Cloudflare, OpenAI, Anthropic, Generic sk-
    ("gemini_key", re.compile(r"AQ\.[A-Za-z0-9_\-]{15,}", re.IGNORECASE)),
    ("groq_key", re.compile(r"gsk_[A-Za-z0-9_\-]{15,}", re.IGNORECASE)),
    ("cloudflare_key", re.compile(r"(?:cfut_|cf_mock_token_)[A-Za-z0-9_\-]{15,}", re.IGNORECASE)),
    ("openai_style_key", re.compile(r"sk-[A-Za-z0-9_\-]{15,}", re.IGNORECASE)),
    ("google_key", re.compile(r"AIzaSy[A-Za-z0-9_\-]{10,}", re.IGNORECASE)),
    # JWT Tokens
    ("jwt_token", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+", re.IGNORECASE)),
    # AWS Credentials
    ("aws_access_key", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")),
    ("aws_secret_key", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?")),
    # Database Connection Strings (Postgres, MySQL, Mongo, Redis, etc.)
    (
        "db_conn_string",
        re.compile(
            r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|sqlite|cockroachdb):\/\/[^\s:]+:[^\s@]+@[^\s\/]+(?:\/[^\s\?\"']*)?",
            re.IGNORECASE,
        ),
    ),
    # Private Keys (RSA, EC, OPENSSH)
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    # Authorization headers & Bearer tokens
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}")),
    ("auth_header", re.compile(r"(?i)authorization\s*[:=]\s*(?:Bearer|Basic)\s+[^\r\n,;\"']+")),
    ("cookie_header", re.compile(r"(?i)cookie\s*[:=]\s*[^\r\n;\"']+")),
    # Passwords & API Secrets in key-value format
    (
        "password_kv",
        re.compile(
            r"(?i)(password|passwd|pwd|client_secret|api_secret|access_token|refresh_token)\s*[:=]\s*['\"]?([^\s'\";,]{4,})['\"]?"
        ),
    ),
    # Environment variable assignments with secrets
    (
        "env_secret",
        re.compile(
            r"(?i)(export\s+)?([A-Z0-9_]*(?:KEY|SECRET|PASSWORD|TOKEN|AUTH|CREDENTIAL)[A-Z0-9_]*\s*=\s*)(['\"]?[^\s'\";]+['\"]?)"
        ),
    ),
]


class SecretRedactor:
    """Detects and redacts confidential credentials and secret strings."""

    REDACTED_SUBSTITUTE: str = "[REDACTED]"

    @classmethod
    def detect_secrets(cls, text: str) -> bool:
        """Returns True if any sensitive token or secret pattern matches."""
        if not text or not isinstance(text, str):
            return False
        for _, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Substitutes all detected secrets with [REDACTED]."""
        if not text or not isinstance(text, str):
            return text

        sanitized = text
        for name, pattern in SECRET_PATTERNS:
            if name == "password_kv":
                sanitized = pattern.sub(rf"\1: {cls.REDACTED_SUBSTITUTE}", sanitized)
            elif name == "env_secret":
                sanitized = pattern.sub(rf"\1\2{cls.REDACTED_SUBSTITUTE}", sanitized)
            elif name == "auth_header":
                sanitized = pattern.sub(f"Authorization: {cls.REDACTED_SUBSTITUTE}", sanitized)
            elif name == "cookie_header":
                sanitized = pattern.sub(f"Cookie: {cls.REDACTED_SUBSTITUTE}", sanitized)
            else:
                sanitized = pattern.sub(cls.REDACTED_SUBSTITUTE, sanitized)

        return sanitized

    @classmethod
    def sanitize_recursive(cls, data: Any) -> Any:
        """Deeply traverses dicts, lists, and strings to redact secrets."""
        if isinstance(data, str):
            return cls.redact_secrets(data)
        elif isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                lower_k = str(k).lower()
                if any(sec_term in lower_k for sec_term in ["secret", "password", "token", "api_key", "credential", "auth"]):
                    clean_dict[k] = cls.REDACTED_SUBSTITUTE
                else:
                    clean_dict[k] = cls.sanitize_recursive(v)
            return clean_dict
        elif isinstance(data, list):
            return [cls.sanitize_recursive(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(cls.sanitize_recursive(item) for item in data)
        return data


def redact_secrets(text: str) -> str:
    return SecretRedactor.redact_secrets(text)


def detect_secrets(text: str) -> bool:
    return SecretRedactor.detect_secrets(text)
