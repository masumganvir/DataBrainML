"""
DataWise AI — File Validation & Security Layer

Enforces strict input validation on all uploaded datasets:
  1. Filename sanitization & path traversal prevention
  2. File extension whitelisting
  3. File size limits
  4. Encoding detection (UTF-8, Latin-1, CP1252, etc.)
  5. CSV delimiter sniffing & structural integrity check
  6. Empty file & zero-row rejection
  7. Malformed row / ragged table detection
  8. Excel (XLSX / XLS) and JSON structural validation
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger

from app.config.settings import get_settings

settings = get_settings()


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation checks."""
    def __init__(self, message: str, code: str = "validation_failed"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class ValidationResult:
    """Detailed summary of file validation results."""
    is_valid: bool
    filename: str
    format: str  # csv, xlsx, xls, json
    size_bytes: int
    encoding: str = "utf-8"
    delimiter: Optional[str] = None
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename against path traversal and dangerous characters.
    Extracts only the basename, removes directory separators and illegal characters.
    """
    if not filename or not filename.strip():
        return "dataset.csv"
    
    # Strip path components
    clean = Path(filename).name
    # Replace dangerous or unwanted chars
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean)
    # Prevent hidden files or leading dots
    clean = clean.lstrip('.')
    # Collapse multiple underscores
    clean = re.sub(r'_+', '_', clean)
    
    if not clean or clean == '.':
        return "dataset.csv"
    return clean


def detect_csv_encoding(content: bytes) -> str:
    """
    Detect text encoding from raw bytes by attempting standard decodings.
    Tries UTF-8, UTF-8-SIG (BOM), Latin-1, and CP1252.
    """
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            content.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"  # Latin-1 decodes arbitrary byte sequences safely


def sniff_csv_delimiter(sample_text: str) -> str:
    """Sniff the most likely CSV delimiter (comma, semicolon, tab, pipe)."""
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text, delimiters=[',', ';', '\t', '|'])
        return dialect.delimiter
    except Exception:
        # Fallback heuristic: count occurrences on first non-empty line
        lines = [line for line in sample_text.splitlines() if line.strip()]
        if lines:
            first_line = lines[0]
            counts = {
                ',': first_line.count(','),
                ';': first_line.count(';'),
                '\t': first_line.count('\t'),
                '|': first_line.count('|'),
            }
            best = max(counts, key=counts.get)
            if counts[best] > 0:
                return best
        return ','


def validate_csv_content(content: bytes, filename: str) -> ValidationResult:
    """Validate CSV structure, delimiter, columns, and rows."""
    size = len(content)
    if size == 0:
        raise FileValidationError("File is empty (0 bytes).", code="empty_file")

    encoding = detect_csv_encoding(content)
    try:
        text = content.decode(encoding)
    except Exception as exc:
        raise FileValidationError(f"Could not decode CSV using {encoding}: {exc}", code="decode_error")

    # Sample first few lines for sniffing
    sample_lines = text.splitlines()[:50]
    sample_text = "\n".join(sample_lines)
    delimiter = sniff_csv_delimiter(sample_text)

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            nrows=5,
            on_bad_lines="error",
        )
    except Exception as exc:
        raise FileValidationError(f"Malformed CSV structure or inconsistent column counts: {exc}", code="malformed_csv")

    if df.empty and len(df.columns) == 0:
        raise FileValidationError("CSV contains no columns or data.", code="empty_data")

    # Read full shape (or count lines quickly)
    try:
        full_df = pd.read_csv(io.StringIO(text), sep=delimiter, on_bad_lines="warn")
    except Exception as exc:
        raise FileValidationError(f"Error reading complete CSV: {exc}", code="malformed_csv")

    if len(full_df) == 0:
        raise FileValidationError("Dataset contains headers but 0 data rows.", code="no_rows")

    warnings = []
    # Check for unnamed or duplicate columns
    cols = [str(c) for c in full_df.columns]
    unnamed = [c for c in cols if c.startswith("Unnamed:")]
    if unnamed:
        warnings.append(f"Found {len(unnamed)} unnamed columns.")
    if len(cols) != len(set(cols)):
        warnings.append("Dataset has duplicate column names.")

    return ValidationResult(
        is_valid=True,
        filename=filename,
        format="csv",
        size_bytes=size,
        encoding=encoding,
        delimiter=delimiter,
        row_count=len(full_df),
        column_count=len(cols),
        columns=cols,
        warnings=warnings,
    )


def validate_excel_content(content: bytes, filename: str, ext: str) -> ValidationResult:
    """Validate XLSX or XLS structure."""
    size = len(content)
    if size == 0:
        raise FileValidationError("File is empty (0 bytes).", code="empty_file")

    try:
        engine = "openpyxl" if ext == "xlsx" else "xlrd"
        df = pd.read_excel(io.BytesIO(content), engine=engine)
    except Exception as exc:
        raise FileValidationError(f"Could not parse Excel spreadsheet: {exc}", code="malformed_excel")

    if len(df.columns) == 0:
        raise FileValidationError("Excel sheet contains no columns.", code="empty_columns")
    if len(df) == 0:
        raise FileValidationError("Excel sheet contains headers but 0 data rows.", code="no_rows")

    cols = [str(c) for c in df.columns]
    warnings = []
    if len(cols) != len(set(cols)):
        warnings.append("Excel sheet contains duplicate column names.")

    return ValidationResult(
        is_valid=True,
        filename=filename,
        format=ext,
        size_bytes=size,
        encoding="binary",
        row_count=len(df),
        column_count=len(cols),
        columns=cols,
        warnings=warnings,
    )


def validate_json_content(content: bytes, filename: str) -> ValidationResult:
    """Validate JSON file structure (expects array of objects or split records)."""
    size = len(content)
    if size == 0:
        raise FileValidationError("File is empty (0 bytes).", code="empty_file")

    encoding = detect_csv_encoding(content)
    try:
        text = content.decode(encoding)
        data = json.loads(text)
    except Exception as exc:
        raise FileValidationError(f"Invalid JSON content: {exc}", code="malformed_json")

    try:
        df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame(data)
    except Exception as exc:
        raise FileValidationError(f"Could not convert JSON to tabular dataset: {exc}", code="json_conversion_error")

    if len(df) == 0:
        raise FileValidationError("JSON dataset has 0 rows.", code="no_rows")
    if len(df.columns) == 0:
        raise FileValidationError("JSON dataset has 0 columns.", code="no_columns")

    cols = [str(c) for c in df.columns]
    return ValidationResult(
        is_valid=True,
        filename=filename,
        format="json",
        size_bytes=size,
        encoding=encoding,
        row_count=len(df),
        column_count=len(cols),
        columns=cols,
    )


def validate_uploaded_file(content: bytes, original_filename: str) -> ValidationResult:
    """
    Main validator entrypoint.
    Executes security, extension, size, and content integrity checks.
    """
    clean_name = sanitize_filename(original_filename)
    ext = clean_name.rsplit(".", 1)[-1].lower() if "." in clean_name else ""

    if ext not in settings.allowed_extensions_set:
        allowed = ", ".join(f".{e}" for e in sorted(settings.allowed_extensions_set))
        raise FileValidationError(
            f"Unsupported file format '{ext}'. Allowed formats: {allowed}",
            code="unsupported_format",
        )

    size = len(content)
    if size > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_mb
        raise FileValidationError(
            f"File size ({size / (1024*1024):.1f} MB) exceeds maximum allowed size ({max_mb} MB).",
            code="file_too_large",
        )

    if ext == "csv":
        return validate_csv_content(content, clean_name)
    elif ext in ("xlsx", "xls"):
        return validate_excel_content(content, clean_name, ext)
    elif ext == "json":
        return validate_json_content(content, clean_name)
    else:
        raise FileValidationError(f"Unsupported format: {ext}", code="unsupported_format")
