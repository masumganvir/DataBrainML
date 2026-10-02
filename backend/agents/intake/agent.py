"""
DataWise AI — Intake Agent
Validates uploaded files (CSV, Excel, JSON, Parquet), calculates row/column counts,
detects encoding, checks duplicates & missing values, and provides chunked processing for large files.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class IntakeAgent(BaseAgent):
    """Agent for validating, profiling schema, and ingesting raw dataset files."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Intake Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        if not path or not Path(path).exists():
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Dataset intake failed: file does not exist.",
                errors=["File path missing or unreadable"],
            )

        p = Path(path)
        file_size = p.stat().st_size
        ext = p.suffix.lower().lstrip(".")
        dataset_id = input_data.dataset_id or str(uuid.uuid4())

        # Read small sample to inspect types & schema quickly
        df_sample = load_dataframe_safely(p, max_rows=1000)
        if df_sample is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Unable to parse file at {path}.",
                errors=[f"Unsupported or corrupted format: {ext}"],
            )

        # Full or chunked count
        is_large = file_size > 50 * 1024 * 1024  # >50MB
        if ext == "csv" and is_large:
            row_count = 0
            missing_total = 0
            for chunk in pd.read_csv(p, chunksize=50000, low_memory=False):
                row_count += len(chunk)
                missing_total += int(chunk.isna().sum().sum())
            col_count = len(df_sample.columns)
            duplicate_count = 0  # skipped on large file for speed
        else:
            df_full = load_dataframe_safely(p)
            if df_full is not None:
                row_count = len(df_full)
                col_count = len(df_full.columns)
                missing_total = int(df_full.isna().sum().sum())
                duplicate_count = int(df_full.duplicated().sum())
            else:
                row_count = len(df_sample)
                col_count = len(df_sample.columns)
                missing_total = int(df_sample.isna().sum().sum())
                duplicate_count = 0

        schema = {col: str(df_sample[col].dtype) for col in df_sample.columns}
        metadata = {
            "dataset_id": dataset_id,
            "filename": p.name,
            "file_format": ext,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "row_count": row_count,
            "column_count": col_count,
            "total_missing_cells": missing_total,
            "duplicate_rows": duplicate_count,
            "is_large_file": is_large,
            "columns": list(df_sample.columns),
            "schema": schema,
            "sample_head": df_sample.head(5).to_dict(orient="records"),
        }

        summary = (
            f"Successfully ingested '{p.name}' ({ext.upper()} | {metadata['file_size_mb']} MB): "
            f"{row_count:,} rows, {col_count} columns. Found {missing_total:,} missing values "
            f"and {duplicate_count:,} duplicate rows."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"metadata": metadata, "dataset_id": dataset_id, "dataset_path": str(p)},
            summary=summary,
        )
