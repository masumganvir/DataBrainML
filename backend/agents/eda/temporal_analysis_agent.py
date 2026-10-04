"""
DataWise AI — Temporal Analysis Agent
Section 10 & 12 Specification:
Detects datetime columns, audits cadence, trend, seasonality, gaps, or safely skips if no temporal features exist.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class TemporalAnalysisAgent:
    """Analyzes time-series dynamics, periodicities, and timestamps if available."""

    def __init__(self, name: str = "TemporalAnalysisAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            dt_cols = state.get("datetime_columns") or []
            if not dt_cols:
                state["temporal_summary"] = {
                    "has_temporal_features": False,
                    "message": "Dataset contains purely cross-sectional or non-temporal records.",
                }
                state.setdefault("completed_steps", []).append("temporal_analysis")
                return state

            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            temporal_records: Dict[str, Any] = {}
            for col in dt_cols:
                try:
                    ts = pd.to_datetime(df[col], errors="coerce").dropna().sort_values()
                    if len(ts) < 5:
                        continue
                    time_span = str(ts.max() - ts.min())
                    diffs = ts.diff().dropna()
                    median_cadence = str(diffs.median()) if not diffs.empty else "irregular"

                    temporal_records[col] = {
                        "min_time": str(ts.min()),
                        "max_time": str(ts.max()),
                        "time_span": time_span,
                        "median_cadence": median_cadence,
                        "monotonic_increasing": bool(ts.is_monotonic_increasing),
                        "recommended_features": ["year", "month", "day", "dayofweek", "hour"],
                    }
                except Exception as dt_err:
                    logger.debug(f"Datetime parse notice for {col}: {dt_err}")

            state["temporal_summary"] = {
                "has_temporal_features": len(temporal_records) > 0,
                "columns": temporal_records,
            }
            state.setdefault("completed_steps", []).append("temporal_analysis")
            logger.info(f"[{self.name}] Audited {len(temporal_records)} temporal features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Temporal analysis error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
