"""
DataWise AI — Ingestion: CSV Loader
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd


def load_csv(
    file_path: str,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
    nrows: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load a CSV file into a pandas DataFrame with structured ingestion metadata."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    encodings_to_try = [encoding] if encoding else ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
    df = None
    used_encoding = "utf-8"

    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            df = pd.read_csv(
                file_path,
                encoding=enc,
                sep=delimiter if delimiter else None,
                engine="python" if delimiter is None else "c",
                nrows=nrows,
                low_memory=False,
            )
            used_encoding = enc
            break
        except (UnicodeDecodeError, Exception):
            continue

    if df is None:
        # Fallback to standard read_csv
        df = pd.read_csv(file_path, low_memory=False, nrows=nrows)

    metadata = {
        "file_path": str(path.resolve()),
        "file_name": path.name,
        "format": "csv",
        "rows": len(df),
        "columns": len(df.columns),
        "encoding": used_encoding,
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
    }
    return df, metadata
