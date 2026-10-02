"""
DataWise AI — Quality & Missing Value Analyzer Tool

Autonomously identifies missing values and duplicates:
  - Missing value severity categorization:
      * NONE: 0%
      * LOW: < 5%
      * MEDIUM: 5% - 20%
      * HIGH: 20% - 50%
      * CRITICAL: > 50%
  - Adaptive imputation strategy recommendations based on column type & skewness:
      * Skewed numeric (|skew| > 1.0) -> median
      * Normal numeric (|skew| <= 1.0) -> mean
      * Low-missing (< 3%) -> drop_rows or mean/median
      * Critical (> 50%) -> drop_column (requires human approval)
      * Categorical -> most_frequent or constant ("Missing")
  - Full duplicate row detection and analysis
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from app.state.data_science_state import MissingValueReport


def classify_missing_severity(pct: float) -> Literal["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
    """Maps missing percentage to defined severity levels."""
    if pct == 0.0:
        return "NONE"
    elif pct < 5.0:
        return "LOW"
    elif pct < 20.0:
        return "MEDIUM"
    elif pct < 50.0:
        return "HIGH"
    else:
        return "CRITICAL"


class QualityAnalyzer:
    """Evaluates data hygiene, missingness patterns, and duplicates."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.total_rows = len(df)
        self.total_cols = len(df.columns)

    def analyze_missing_values(self) -> List[MissingValueReport]:
        """Generates comprehensive MissingValueReport for all columns."""
        reports: List[MissingValueReport] = []

        for col in self.df.columns:
            s = self.df[col]
            missing_count = int(s.isnull().sum())
            missing_pct = round((missing_count / self.total_rows * 100), 2) if self.total_rows > 0 else 0.0
            severity = classify_missing_severity(missing_pct)

            dtype_str = str(s.dtype)
            is_numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)

            # Determine recommendations
            recommended, alternatives, explanation = self._recommend_imputation(
                col=str(col),
                s=s,
                missing_pct=missing_pct,
                severity=severity,
                is_numeric=is_numeric,
            )

            report: MissingValueReport = {
                "column": str(col),
                "missing_count": missing_count,
                "missing_pct": missing_pct,
                "dtype": dtype_str,
                "severity": severity,
                "recommended_strategy": recommended,
                "alternative_strategies": alternatives,
                "explanation": explanation,
            }
            reports.append(report)

        return reports

    def analyze_duplicates(self) -> Dict[str, Any]:
        """Identifies duplicate rows and returns metrics and examples."""
        dup_mask = self.df.duplicated(keep="first")
        dup_count = int(dup_mask.sum())
        dup_pct = round((dup_count / self.total_rows * 100), 2) if self.total_rows > 0 else 0.0

        sample_duplicates: List[Dict[str, Any]] = []
        if dup_count > 0:
            dup_rows = self.df[dup_mask].head(5)
            sample_duplicates = json.loads(dup_rows.to_json(orient="records", date_format="iso"))

        return {
            "has_duplicates": dup_count > 0,
            "duplicate_count": dup_count,
            "duplicate_pct": dup_pct,
            "sample_duplicates": sample_duplicates,
            "recommendation": (
                "Drop exact duplicate rows to prevent data leakage and inflated evaluation scores."
                if dup_count > 0
                else "No duplicate rows detected. Dataset integrity intact."
            ),
        }

    def _recommend_imputation(
        self,
        col: str,
        s: pd.Series,
        missing_pct: float,
        severity: str,
        is_numeric: bool,
    ) -> Tuple[str, List[str], str]:
        """Generates domain-aware imputation recommendation."""
        if severity == "NONE":
            return "none", [], "No missing values present."

        if severity == "CRITICAL":
            return (
                "drop_column",
                ["indicator_and_impute", "constant"],
                f"Column '{col}' has {missing_pct}% missing values. Dropping is recommended because over half the values are absent, which could introduce substantial synthetic bias if imputed.",
            )

        if is_numeric:
            non_null = s.dropna()
            skew = float(non_null.skew()) if len(non_null) > 2 else 0.0

            if abs(skew) > 1.0:
                return (
                    "median",
                    ["mean", "knn", "constant"],
                    f"Column '{col}' is skewed (skewness = {skew:.2f}). Median imputation is recommended to maintain robustness against extreme outliers.",
                )
            else:
                return (
                    "mean",
                    ["median", "knn", "constant"],
                    f"Column '{col}' has an approximately symmetric distribution (skewness = {skew:.2f}). Mean imputation preserves the expected value.",
                )
        else:
            # Categorical or string
            return (
                "most_frequent",
                ["constant", "missing_category"],
                f"Categorical column '{col}'. Mode (most frequent) imputation is recommended for low-to-medium missingness.",
            )


def analyze_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Helper entry point for comprehensive quality and missing value scan."""
    analyzer = QualityAnalyzer(df)
    missing_reports = analyzer.analyze_missing_values()
    duplicates_report = analyzer.analyze_duplicates()

    total_missing_cells = sum(r["missing_count"] for r in missing_reports)
    total_cells = len(df) * len(df.columns) if len(df) > 0 else 0
    overall_missing_pct = round((total_missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

    columns_with_missing = [r for r in missing_reports if r["missing_count"] > 0]

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "total_missing_cells": total_missing_cells,
        "overall_missing_pct": overall_missing_pct,
        "columns_with_missing_count": len(columns_with_missing),
        "missing_reports": missing_reports,
        "duplicates": duplicates_report,
    }


class MissingReportList(list):
    """List of missing value reports supporting column name 'in' membership check."""
    def __contains__(self, item: Any) -> bool:
        if super().__contains__(item):
            return True
        for elem in self:
            if isinstance(elem, dict) and elem.get("column") == item:
                return True
        return False


def detect_missing_values(df: pd.DataFrame) -> MissingReportList:
    return MissingReportList(QualityAnalyzer(df).analyze_missing_values())



def detect_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
    return QualityAnalyzer(df).analyze_duplicates()


def run_quality_checks(df: pd.DataFrame) -> Dict[str, Any]:
    return analyze_data_quality(df)

