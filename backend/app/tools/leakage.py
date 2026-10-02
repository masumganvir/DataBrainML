"""
DataWise AI — Data Leakage Detection Tool

Detects multiple categories of data leakage:
  1. Perfect / near-perfect correlation with target → direct leakage
  2. Columns derived from the target (e.g., ID columns correlated to target)
  3. Temporal leakage: future-dated columns used to predict the past
  4. Identifier columns that may memorize samples
  5. High-cardinality free-text columns that encode target
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


DIRECT_LEAKAGE_THRESHOLD = 0.98   # correlation ≥ 98% with target
NEAR_LEAKAGE_THRESHOLD = 0.90     # correlation ≥ 90% (warning)


class LeakageDetector:
    """Scans dataset for features that constitute or risk data leakage."""

    def __init__(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> None:
        self.df = df
        self.target_column = target_column
        self.task_type = task_type

        self.feature_cols = [c for c in df.columns if c != target_column]
        self._numeric_df = self._to_numeric(df[self.feature_cols])

    # -------------------------------------------------------------- #
    #  Public API
    # -------------------------------------------------------------- #

    def detect(self) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []

        # 1. Correlation-based leakage (only if target known)
        if self.target_column and self.target_column in self.df.columns:
            corr_warnings = self._correlation_leakage()
            warnings.extend(corr_warnings)

        # 2. Identifier column leakage
        id_warnings = self._identifier_leakage()
        warnings.extend(id_warnings)

        # 3. Temporal leakage heuristic
        temporal_warnings = self._temporal_leakage()
        warnings.extend(temporal_warnings)

        # 4. Target-derived / post-event columns
        derived_warnings = self._derived_column_leakage()
        warnings.extend(derived_warnings)

        # 5. Free-text memorization risk
        freetext_warnings = self._free_text_leakage()
        warnings.extend(freetext_warnings)

        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for w in warnings:
            s = w.get("severity", "LOW")
            if s in severity_counts:
                severity_counts[s] += 1

        return {
            "total_warnings": len(warnings),
            "severity_counts": severity_counts,
            "warnings": warnings,
            "clean": len(warnings) == 0,
            "summary": self._summary(warnings),
        }

    run_all = detect

    # -------------------------------------------------------------- #
    #  Private: leakage detectors

    # -------------------------------------------------------------- #

    def _correlation_leakage(self) -> List[Dict[str, Any]]:
        warnings = []
        try:
            target = self.df[self.target_column]
            if target.dtype == object or str(target.dtype) == "category":
                target_enc = target.astype("category").cat.codes
            else:
                target_enc = pd.to_numeric(target, errors="coerce")

            for col in self._numeric_df.columns:
                try:
                    col_series = self._numeric_df[col].fillna(0)
                    if col_series.nunique() < 2:
                        continue
                    r = abs(float(np.corrcoef(col_series, target_enc.fillna(0))[0, 1]))
                    if np.isnan(r):
                        continue
                    if r >= DIRECT_LEAKAGE_THRESHOLD:
                        warnings.append({
                            "column": col,
                            "severity": "CRITICAL",
                            "leakage_type": "direct_correlation",
                            "correlation": round(r, 4),
                            "message": (
                                f"Column '{col}' has near-perfect correlation (r={r:.4f}) with target "
                                f"'{self.target_column}'. This almost certainly constitutes direct data leakage."
                            ),
                            "recommendation": f"Remove '{col}' from feature set immediately.",
                        })
                    elif r >= NEAR_LEAKAGE_THRESHOLD:
                        warnings.append({
                            "column": col,
                            "severity": "HIGH",
                            "leakage_type": "near_perfect_correlation",
                            "correlation": round(r, 4),
                            "message": (
                                f"Column '{col}' is highly correlated with target (r={r:.4f}). "
                                f"Investigate whether this feature is available at prediction time."
                            ),
                            "recommendation": "Verify temporal order and availability at inference.",
                        })
                except Exception:  # noqa: BLE001
                    continue
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Correlation leakage check failed: {exc}")
        return warnings

    def _identifier_leakage(self) -> List[Dict[str, Any]]:
        warnings = []
        id_pattern = re.compile(r"(^id$|_id$|uuid|key|index|row_num|record)", re.IGNORECASE)
        for col in self.feature_cols:
            if id_pattern.search(col):
                n_unique = self.df[col].nunique()
                if n_unique > len(self.df) * 0.8:
                    warnings.append({
                        "column": col,
                        "severity": "HIGH",
                        "leakage_type": "identifier_memorization",
                        "message": (
                            f"Column '{col}' appears to be a unique identifier "
                            f"({n_unique}/{len(self.df)} unique values). "
                            f"Models trained on identifiers memorize training data and fail on new records."
                        ),
                        "recommendation": f"Exclude '{col}' from features.",
                    })
        return warnings

    def _temporal_leakage(self) -> List[Dict[str, Any]]:
        """Warn about future-looking datetime columns."""
        warnings = []
        future_kws = re.compile(r"(future|next|after|end|close|complete|final)", re.IGNORECASE)
        for col in self.feature_cols:
            if future_kws.search(col):
                warnings.append({
                    "column": col,
                    "severity": "MEDIUM",
                    "leakage_type": "temporal_leakage_risk",
                    "message": (
                        f"Column '{col}' has a name suggesting future information "
                        f"('future', 'next', 'after', etc.). Verify this feature is observable "
                        f"at the time of prediction to avoid target leakage."
                    ),
                    "recommendation": "Confirm this feature is available at inference time.",
                })
        return warnings

    def _derived_column_leakage(self) -> List[Dict[str, Any]]:
        """Detect columns likely derived from or encoding the target."""
        warnings = []
        if not self.target_column:
            return warnings
        target_base = self.target_column.lower().replace("_", "").replace(" ", "")
        for col in self.feature_cols:
            col_base = col.lower().replace("_", "").replace(" ", "")
            if target_base in col_base or col_base in target_base:
                if col != self.target_column:
                    warnings.append({
                        "column": col,
                        "severity": "HIGH",
                        "leakage_type": "target_derived_name",
                        "message": (
                            f"Column '{col}' name is similar to target '{self.target_column}'. "
                            f"This may be a derived, encoded, or transformed version of the target."
                        ),
                        "recommendation": f"Carefully audit whether '{col}' is computed from the target.",
                    })
        return warnings

    def _free_text_leakage(self) -> List[Dict[str, Any]]:
        """Warn about high-cardinality text columns that may encode target."""
        warnings = []
        for col in self.feature_cols:
            if self.df[col].dtype != object:
                continue
            n_unique = self.df[col].nunique()
            if n_unique > len(self.df) * 0.5:
                avg_len = self.df[col].dropna().astype(str).str.len().mean()
                if avg_len > 50:
                    warnings.append({
                        "column": col,
                        "severity": "MEDIUM",
                        "leakage_type": "free_text_memorization",
                        "message": (
                            f"Column '{col}' is a high-cardinality free-text field "
                            f"({n_unique} unique values, avg {avg_len:.0f} chars). "
                            f"Without proper hashing, models can memorize training examples."
                        ),
                        "recommendation": "Use TF-IDF/hashing or exclude from features.",
                    })
        return warnings

    # -------------------------------------------------------------- #
    #  Private: helpers
    # -------------------------------------------------------------- #

    def _to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in out.select_dtypes(include=["object", "category"]).columns:
            out[col] = out[col].astype("category").cat.codes.replace(-1, np.nan)
        for col in out.select_dtypes(include=["datetime64"]).columns:
            out[col] = out[col].astype(np.int64) // 10**9
        return out.select_dtypes(include=[np.number])

    def _summary(self, warnings: List[Dict[str, Any]]) -> str:
        if not warnings:
            return "No leakage risks detected. The dataset appears safe for ML training."
        critical = [w for w in warnings if w.get("severity") == "CRITICAL"]
        high = [w for w in warnings if w.get("severity") == "HIGH"]
        if critical:
            return (
                f"⚠️ CRITICAL: {len(critical)} direct leakage column(s) detected "
                f"({', '.join(w['column'] for w in critical)}). Remove before training."
            )
        elif high:
            return (
                f"⚠️ HIGH: {len(high)} potential leakage risk(s) detected. "
                f"Careful review required before model training."
            )
        return f"Leakage scan found {len(warnings)} low/medium warnings. Review recommended."
