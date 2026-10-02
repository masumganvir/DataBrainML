"""
DataWise AI — Storage Abstraction Layer

Handles file persistence and immutable dataset versioning:
  - Preserves original uploaded dataset intact (never overwritten)
  - Organizes versions: original -> analysis -> preprocessed -> feature_engineered -> final
  - Supports CSV, Excel, and JSON loading and saving
  - Provides paginated preview with schema detection
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from app.config.settings import get_settings

settings = get_settings()


class StorageManager:
    """Manages file storage and data persistence for sessions and datasets."""

    def __init__(self, upload_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or settings.upload_dir_path
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def get_session_dir(self, session_id: str) -> Path:
        """Returns and ensures the session-specific upload directory."""
        path = self.upload_dir / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_uploaded_bytes(
        self,
        session_id: str,
        version: str,
        sanitized_filename: str,
        content: bytes,
    ) -> Tuple[str, str]:
        """
        Saves raw bytes into the session directory under a versioned name.
        Returns (absolute_file_path, stored_filename).
        """
        session_dir = self.get_session_dir(session_id)
        stored_filename = f"{version}_{sanitized_filename}"
        file_path = session_dir / stored_filename

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved dataset version '{version}' for session {session_id} -> {file_path}")
        return str(file_path.resolve()), stored_filename

    def save_dataframe(
        self,
        df: pd.DataFrame,
        session_id: str,
        version: str,
        base_name: str = "dataset.csv",
        file_format: str = "csv",
    ) -> Tuple[str, str]:
        """
        Saves a pandas DataFrame to disk under a specific version.
        Returns (absolute_file_path, stored_filename).
        """
        session_dir = self.get_session_dir(session_id)
        # Ensure clean extension
        ext = file_format.lower().lstrip(".")
        clean_base = Path(base_name).stem + f".{ext}"
        stored_filename = f"{version}_{clean_base}"
        file_path = session_dir / stored_filename

        if ext == "csv":
            df.to_csv(file_path, index=False)
        elif ext in ("xlsx", "xls"):
            df.to_excel(file_path, index=False)
        elif ext == "json":
            df.to_json(file_path, orient="records", indent=2)
        else:
            # Fallback to csv
            file_path = file_path.with_suffix(".csv")
            stored_filename = f"{version}_{Path(base_name).stem}.csv"
            df.to_csv(file_path, index=False)

        logger.info(f"Saved DataFrame version '{version}' ({len(df)} rows) -> {file_path}")
        return str(file_path.resolve()), stored_filename

    def load_dataframe(self, file_path: str, file_format: Optional[str] = None) -> pd.DataFrame:
        """
        Loads a pandas DataFrame from disk.
        Auto-infers format if not provided.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        ext = (file_format or path.suffix).lower().lstrip(".")

        if ext == "csv":
            # Auto-sniff delimiter
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                sample = f.read(4096)
            from app.security.file_validator import sniff_csv_delimiter
            sep = sniff_csv_delimiter(sample)
            return pd.read_csv(path, sep=sep, low_memory=False)
        elif ext in ("xlsx", "xls"):
            engine = "openpyxl" if ext == "xlsx" else "xlrd"
            return pd.read_excel(path, engine=engine)
        elif ext == "json":
            return pd.read_json(path)
        elif ext in ("parquet", "pq"):
            return pd.read_parquet(path)
        else:
            # Try CSV fallback
            return pd.read_csv(path, low_memory=False)

    def get_dataset_preview(
        self,
        file_path: str,
        file_format: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Returns a paginated slice of rows with schema info and null counts.
        """
        df = self.load_dataframe(file_path, file_format)
        total_rows = len(df)
        total_cols = len(df.columns)

        # Slice
        sliced = df.iloc[offset : offset + limit]

        # Convert numpy/pandas NaN / inf to None for clean JSON serialization
        records = json.loads(sliced.to_json(orient="records", date_format="iso"))

        # Column metadata
        columns = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())
            null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0
            columns.append({
                "name": str(col),
                "dtype": dtype_str,
                "null_count": null_count,
                "null_percentage": null_pct,
                "unique_count": int(df[col].nunique(dropna=True)),
            })

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "limit": limit,
            "offset": offset,
            "columns": columns,
            "rows": records,
        }


    def save_processed_dataframe(
        self,
        df: pd.DataFrame,
        session_id: str,
        version: str = "processed",
    ) -> str:
        """
        Saves a processed DataFrame and returns the absolute file path.
        Convenience wrapper used by advanced analysis endpoints.
        """
        path, _ = self.save_dataframe(df, session_id, version=version)
        return path

    def get_artifacts_dir(self, session_id: str) -> str:
        """Return the path to the session's artifacts directory (creating it if needed)."""
        artifact_root = settings.upload_dir_path.parent / "artifacts" / session_id
        artifact_root.mkdir(parents=True, exist_ok=True)
        return str(artifact_root)


# Singleton instance for application use
storage_manager = StorageManager()


def load_dataset_file(file_path: str, file_format: Optional[str] = None) -> pd.DataFrame:
    return storage_manager.load_dataframe(file_path, file_format)


def save_dataset_file(
    df: pd.DataFrame, session_id: str, version: str = "v1", base_name: str = "dataset.csv"
) -> Tuple[str, str]:
    return storage_manager.save_dataframe(df, session_id, version=version, base_name=base_name)


def get_dataset_metadata(file_path: str) -> Dict[str, Any]:
    return storage_manager.get_dataset_preview(file_path, limit=5)

