"""
Context Sanitizer & Output Security Gate
Guarantees that no internal secrets, raw stack traces, private filesystem paths,
PII, or system prompts leak into user responses, APIs, reports, or notebooks.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple, Union
from recovery.secret_redactor import SecretRedactor
from recovery.pii_redactor import PIIRedactor

# File path redaction pattern (Windows and Unix absolute paths)
PATH_PATTERN = re.compile(
    r"(?:[a-zA-Z]:[\\/](?:Users|home|root|var|etc|opt|tmp|private)[\\/][^\s'\":;]+)|(?:\/(?:Users|home|root|var|etc|opt|tmp|private)\/[^\s'\":;]+)",
    re.IGNORECASE,
)

# Python traceback pattern
TRACEBACK_PATTERN = re.compile(
    r"Traceback \(most recent call last\):[\s\S]*?(?:(?:Error|Exception|Interrupt):[^\r\n]*)",
    re.MULTILINE,
)

# System prompt / internal instructions leak patterns
PROMPT_LEAK_PATTERNS = [
    re.compile(r"(?i)you are an AI assistant designed by[\s\S]*?(?:instructions|guidelines):?"),
    re.compile(r"(?i)<SYSTEM_INSTRUCTIONS>[\s\S]*?</SYSTEM_INSTRUCTIONS>"),
    re.compile(r"(?i)hidden system prompt:?"),
]

# XSS & Markdown Script Injection patterns
XSS_DANGEROUS_TAGS = re.compile(r"(?i)<\/?(script|iframe|object|embed|svg)\b[^>]*>")
XSS_EVENT_HANDLERS = re.compile(r"(?i)\s+on[a-z]+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)")
JAVASCRIPT_URI_PATTERN = re.compile(r"(?i)javascript:[^\s'\">]+")


class OutputSecurityGate:
    """Final defense gate applied to any outgoing payload, error, log, or artifact."""

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitizes text by stripping secrets, PII, tracebacks, internal paths, and XSS scripts."""
        if not text or not isinstance(text, str):
            return text

        # 1. Redact secrets
        clean = SecretRedactor.redact_secrets(text)

        # 2. Redact PII
        clean = PIIRedactor.redact_pii(clean)

        # 3. Strip raw python tracebacks
        clean = TRACEBACK_PATTERN.sub(
            "[Stack trace hidden for security. Refer to internal Error ID for diagnostics.]",
            clean,
        )

        # 4. Strip internal filesystem paths
        clean = PATH_PATTERN.sub("[INTERNAL_PATH]", clean)

        # 5. Redact prompt instruction leaks
        for pattern in PROMPT_LEAK_PATTERNS:
            clean = pattern.sub("[SYSTEM_INSTRUCTIONS_PROTECTED]", clean)

        # 6. Neutralize XSS script tags, dangerous HTML elements, event handlers, and javascript URIs
        clean = XSS_DANGEROUS_TAGS.sub("", clean)
        clean = XSS_EVENT_HANDLERS.sub("", clean)
        clean = JAVASCRIPT_URI_PATTERN.sub("#blocked", clean)

        return clean

    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """Recursively sanitizes data structures (dict, list, str, etc.)."""
        if isinstance(data, str):
            return cls.sanitize_text(data)
        elif isinstance(data, dict):
            sanitized_dict = {}
            for k, v in data.items():
                sanitized_k = cls.sanitize_text(str(k))
                sanitized_dict[sanitized_k] = cls.sanitize(v)
            return sanitized_dict
        elif isinstance(data, list):
            return [cls.sanitize(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(cls.sanitize(item) for item in data)
        return data

    @classmethod
    def validate_safety(cls, data: Any) -> Tuple[bool, List[str]]:
        """
        Inspects content for security risks.
        Returns (is_safe, list_of_violations).
        """
        violations: List[str] = []
        text_repr = json.dumps(data) if not isinstance(data, str) else data

        if SecretRedactor.detect_secrets(text_repr):
            violations.append("Confidential secret or credential detected")

        if PIIRedactor.detect_pii(text_repr):
            violations.append("Personally Identifiable Information (PII) detected")

        if TRACEBACK_PATTERN.search(text_repr):
            violations.append("Raw traceback detected in outgoing payload")

        return (len(violations) == 0, violations)

    @classmethod
    def block_if_unsafe(cls, data: Any) -> Any:
        """Sanitizes thoroughly. If critical violations cannot be sanitized, blocks."""
        is_safe, violations = cls.validate_safety(data)
        if not is_safe:
            # Force thorough sanitization
            cleaned = cls.sanitize(data)
            # Second check
            still_safe, remaining = cls.validate_safety(cleaned)
            if not still_safe:
                return {
                    "error": "CONTENT_SECURITY_VIOLATION",
                    "message": "Output blocked due to security policy enforcement.",
                    "details": remaining,
                }
            return cleaned
        return data

    @classmethod
    def sanitize_notebook(cls, notebook_content: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Sanitizes Jupyter notebook JSON or string, stripping hardcoded keys and outputs."""
        if isinstance(notebook_content, str):
            try:
                nb_dict = json.loads(notebook_content)
                sanitized_dict = cls.sanitize_notebook(nb_dict)
                return json.dumps(sanitized_dict, indent=2)
            except Exception:
                return cls.sanitize_text(notebook_content)

        if not isinstance(notebook_content, dict):
            return notebook_content

        # Deep sanitize cells
        if "cells" in notebook_content and isinstance(notebook_content["cells"], list):
            for cell in notebook_content["cells"]:
                if "source" in cell:
                    if isinstance(cell["source"], list):
                        cell["source"] = [cls.sanitize_text(line) for line in cell["source"]]
                    elif isinstance(cell["source"], str):
                        cell["source"] = cls.sanitize_text(cell["source"])
                if "outputs" in cell and isinstance(cell["outputs"], list):
                    for output in cell["outputs"]:
                        if "text" in output:
                            if isinstance(output["text"], list):
                                output["text"] = [cls.sanitize_text(line) for line in output["text"]]
                            elif isinstance(output["text"], str):
                                output["text"] = cls.sanitize_text(output["text"])
                        if "traceback" in output:
                            output["traceback"] = ["[Traceback redacted for security]"]

        return notebook_content

    @classmethod
    def sanitize_code(cls, code_str: str) -> str:
        """Sanitizes generated python code, replacing hardcoded credentials with env var lookups."""
        sanitized = SecretRedactor.redact_secrets(code_str)
        # Convert any redacted API assignments into os.environ.get
        sanitized = re.sub(
            r'([A-Z0-9_]*KEY|[A-Z0-9_]*TOKEN)\s*=\s*\[REDACTED\]',
            r'\1 = os.environ.get("\1", "")',
            sanitized,
        )
        return sanitized

    @classmethod
    def sanitize_report(cls, report_text: str) -> str:
        """Sanitizes PDF/HTML/Markdown reports."""
        return cls.sanitize_text(report_text)
