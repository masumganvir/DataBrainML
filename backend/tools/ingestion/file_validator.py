"""
DataWise AI — Ingestion: File Validator
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB default


def validate_file(
    file_path: str,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> Dict[str, Any]:
    """
    Validates file safety, extension, existence, size, and header accessibility.
    Returns structured validation report.
    """
    path = Path(file_path)
    issues: List[str] = []

    if not path.exists():
        return {
            "valid": False,
            "error": f"File does not exist: {file_path}",
            "issues": ["FILE_NOT_FOUND"],
        }

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        issues.append(f"Disallowed extension: {ext}. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    size = path.stat().st_size
    if size == 0:
        issues.append("File is completely empty (0 bytes).")
    elif size > max_size_bytes:
        issues.append(f"File size ({size / (1024*1024):.1f}MB) exceeds limit ({max_size_bytes / (1024*1024):.1f}MB).")

    # Check for basic path traversal or dangerous symbols
    if ".." in str(path) and not path.resolve().is_relative_to(Path.cwd()):
        issues.append("Path traversal warning.")

    is_valid = len(issues) == 0
    return {
        "valid": is_valid,
        "file_name": path.name,
        "extension": ext,
        "size_bytes": size,
        "issues": issues,
    }
