"""
DataWise AI — Ingestion: JSON Loader
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd


def load_json(
    file_path: str,
    orient: Optional[str] = None,
    nrows: Optional[int] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load JSON/JSONL dataset with orientation auto-detection."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Try standard or lines
    df = None
    used_orient = orient or "records"
    try:
        df = pd.read_json(file_path, orient=orient, nrows=nrows)
    except Exception:
        # Fallback lines=True for JSONL
        try:
            df = pd.read_json(file_path, lines=True, nrows=nrows)
            used_orient = "lines"
        except Exception as exc:
            raise ValueError(f"Unable to parse JSON file {file_path}: {exc}") from exc

    metadata = {
        "file_path": str(path.resolve()),
        "file_name": path.name,
        "format": "json",
        "orient": used_orient,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
    }
    return df, metadata
