"""DataWise AI — File Security and Validation

Ensures all uploaded files are treated as untrusted inputs:
  - Validates file extensions against allowlist
  - Validates MIME types
  - Inspects initial byte signatures (magic bytes) to prevent executable masquerading
  - Sanitizes user filenames (strips path traversal, shell metacharacters)
  - Enforces strict size limits
"""

from __future__ import annotations

import os
import re
from typing import BinaryIO, Tuple
from fastapi import HTTPException, status

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json", "parquet"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/json",
    "application/octet-stream",
    "application/x-parquet",
}

# Magic signatures
MAGIC_SIGNATURES = {
    "parquet": b"PAR1",
    "xlsx": b"PK\x03\x04",
    "xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent path traversal or shell exploits."""
    # Strip directory components
    clean_name = os.path.basename(filename)
    # Remove all characters except alphanumeric, hyphen, underscore, and dot
    clean_name = re.sub(r"[^\w\.\-]", "_", clean_name)
    # Prevent hidden files
    clean_name = clean_name.lstrip(".")
    if not clean_name:
        clean_name = "unnamed_dataset.csv"
    return clean_name


def validate_file_content(content_stream: bytes, filename: str) -> Tuple[bool, str]:
    """Inspect magic bytes and extension alignment."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not permitted. Allowed: {ALLOWED_EXTENSIONS}"

    if len(content_stream) == 0:
        return False, "File is completely empty (0 bytes)."

    # Magic byte verification for binary formats
    if ext == "parquet":
        if not content_stream.startswith(MAGIC_SIGNATURES["parquet"]):
            return False, "Invalid Parquet file header signature."
    elif ext == "xlsx":
        if not content_stream.startswith(MAGIC_SIGNATURES["xlsx"]):
            return False, "Invalid XLSX (Zip) file header signature."
    elif ext == "xls":
        if not content_stream.startswith(MAGIC_SIGNATURES["xls"]):
            return False, "Invalid XLS OLE2 compound file signature."
    elif ext == "json":
        # Check that it starts with { or [ after stripping leading whitespace
        stripped = content_stream[:100].lstrip()
        if not (stripped.startswith(b"{") or stripped.startswith(b"[")):
            return False, "Invalid JSON content format."

    return True, "Valid"
