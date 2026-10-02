"""
DataWise AI — Outlier Analyzer Tool

Detects and quantifies univariate and multivariate outliers:
  - Methods:
      1. IQR (Interquartile Range - 1.5x mild, 3.0x extreme)
      2. Z-score (standard score > 3.0)
      3. MAD (Median Absolute Deviation - robust modified Z-score > 3.5)
      4. Isolation Forest (unsupervised tree ensemble)
  - Severity Classification:
      * none: 0%
      * mild: < 2%
      * moderate: 2% - 5%
      * severe: > 5%
  - Per-column outlier reports with lower/upper boundaries and actionable interpretations
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import IsolationForest

from app.state.data_science_state import OutlierReport


def classify_outlier_severity(pct: float) -> Literal["none", "mild", "moderate", "severe"]:
    """Maps outlier percentage to severity levels."""
    if pct == 0.0:
        return "none"
    elif pct < 2.0:
        return "mild"
    elif pct <= 5.0:
        return "moderate"
    else:
        return "severe"


class OutlierAnalyzer:
    """Analyzes outliers across numerical columns using multiple statistical and ML methods."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.total_rows = len(df)
        self.numerical_cols = [
            str(col) for col in df.columns
            if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col])
        ]

    def analyze_iqr(self, multiplier: float = 1.5) -> List[OutlierReport]:
        """Detects outliers using standard or extreme IQR bounds."""
        reports: List[OutlierReport] = []

        for col in self.numerical_cols:
            s = self.df[col].dropna()
            if len(s) < 4:
                continue

            q1 = float(np.percentile(s, 25))
            q3 = float(np.percentile(s, 75))
            iqr = q3 - q1

            lower_bound = round(q1 - multiplier * iqr, 4)
            upper_bound = round(q3 + multiplier * iqr, 4)

            outlier_mask = (s < lower_bound) | (s > upper_bound)
            count = int(outlier_mask.sum())
            pct = round((count / len(s) * 100), 2) if len(s) > 0 else 0.0
            severity = classify_outlier_severity(pct)

            interpretation = self._generate_interpretation(col, count, pct, severity, "IQR", lower_bound, upper_bound)

            reports.append({
                "column": col,
                "method": f"IQR (x{multiplier})",
                "outlier_count": count,
                "outlier_pct": pct,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "severity": severity,
                "interpretation": interpretation,
            })

        return reports

    def analyze_zscore(self, threshold: float = 3.0) -> List[OutlierReport]:
        """Detects outliers using classic Z-score (|Z| > threshold)."""
        reports: List[OutlierReport] = []

        for col in self.numerical_cols:
            s = self.df[col].dropna()
            if len(s) < 4:
                continue

            std_val = float(s.std(ddof=1))
            if std_val == 0:
                continue

            mean_val = float(s.mean())
            z_scores = np.abs((s - mean_val) / std_val)
            outlier_mask = z_scores > threshold

            count = int(outlier_mask.sum())
            pct = round((count / len(s) * 100), 2) if len(s) > 0 else 0.0
            severity = classify_outlier_severity(pct)

            lower_bound = round(mean_val - threshold * std_val, 4)
            upper_bound = round(mean_val + threshold * std_val, 4)
            interpretation = self._generate_interpretation(col, count, pct, severity, "Z-Score", lower_bound, upper_bound)

            reports.append({
                "column": col,
                "method": f"Z-Score (threshold={threshold})",
                "outlier_count": count,
                "outlier_pct": pct,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "severity": severity,
                "interpretation": interpretation,
            })

        return reports

    def analyze_mad(self, threshold: float = 3.5) -> List[OutlierReport]:
        """Detects outliers using Median Absolute Deviation (robust modified Z-score)."""
        reports: List[OutlierReport] = []

        for col in self.numerical_cols:
            s = self.df[col].dropna()
            if len(s) < 4:
                continue

            med = float(s.median())
            abs_dev = np.abs(s - med)
            mad = float(np.median(abs_dev))
            if mad == 0:
                mad = float(np.mean(abs_dev))
            if mad == 0:
                continue

            # Modified Z-score = 0.6745 * (x - med) / mad
            mod_z = 0.6745 * abs_dev / mad
            outlier_mask = mod_z > threshold

            count = int(outlier_mask.sum())
            pct = round((count / len(s) * 100), 2) if len(s) > 0 else 0.0
            severity = classify_outlier_severity(pct)

            cutoff_delta = threshold * mad / 0.6745
            lower_bound = round(med - cutoff_delta, 4)
            upper_bound = round(med + cutoff_delta, 4)
            interpretation = self._generate_interpretation(col, count, pct, severity, "MAD", lower_bound, upper_bound)

            reports.append({
                "column": col,
                "method": f"MAD (threshold={threshold})",
                "outlier_count": count,
                "outlier_pct": pct,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "severity": severity,
                "interpretation": interpretation,
            })

        return reports

    def analyze_isolation_forest(self, contamination: float = 0.03) -> Dict[str, Any]:
        """Runs multi-feature or high-dimensional Isolation Forest."""
        if len(self.numerical_cols) == 0 or self.total_rows < 10:
            return {
                "method": "Isolation Forest",
                "contamination_param": contamination,
                "outlier_count": 0,
                "outlier_pct": 0.0,
                "sample_outlier_indices": [],
                "severity": "none",
                "recommendation": "Dataset too small (<10 rows) for unsupervised Isolation Forest.",
            }

        sub_df = self.df[self.numerical_cols].fillna(self.df[self.numerical_cols].median())
        iso = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        preds = iso.fit_predict(sub_df)
        outlier_indices = np.where(preds == -1)[0].tolist()
        count = len(outlier_indices)
        pct = round((count / self.total_rows * 100), 2)

        return {
            "method": "Isolation Forest",
            "contamination_param": contamination,
            "outlier_count": count,
            "outlier_pct": pct,
            "sample_outlier_indices": outlier_indices[:15],
            "severity": classify_outlier_severity(pct),
            "recommendation": (
                "Multivariate anomalies detected by Isolation Forest. Consider investigating unusual feature combinations before model training."
                if count > 0 else "No significant multivariate anomalies flagged by Isolation Forest."
            ),
        }

    def _generate_interpretation(
        self,
        col: str,
        count: int,
        pct: float,
        severity: str,
        method: str,
        lower: float,
        upper: float,
    ) -> str:
        if count == 0:
            return f"No outliers detected in '{col}' using {method}."
        if severity == "mild":
            return f"Found {count} ({pct}%) mild outliers outside [{lower}, {upper}]. Suggest using RobustScaler or tree-based algorithms invariant to outliers."
        elif severity == "moderate":
            return f"Found {count} ({pct}%) moderate outliers in '{col}'. Winsorizing (clipping at 1st/99th percentile) or quantile transformation is advised."
        else:
            return f"Found {count} ({pct}%) severe outliers in '{col}'. Investigate data entry or measurement errors; clipping or log transformation is strongly recommended."


from app.tools.outlier_decision_engine import OutlierDecisionEngine, analyze_outlier_decisions


def analyze_dataset_outliers(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    domain: Optional[str] = None,
    objective: Optional[str] = None,
) -> Dict[str, Any]:
    """Complete outlier suite combining IQR, Z-score, MAD, Isolation Forest, and Contextual Decision Engine."""
    analyzer = OutlierAnalyzer(df)
    iqr_reports = analyzer.analyze_iqr(multiplier=1.5)
    zscore_reports = analyzer.analyze_zscore(threshold=3.0)
    mad_reports = analyzer.analyze_mad(threshold=3.5)
    iso_report = analyzer.analyze_isolation_forest(contamination=0.03)

    decision_results = analyze_outlier_decisions(
        df=df, target_col=target_col, domain=domain, objective=objective
    )

    return {
        "numerical_columns_analyzed": analyzer.numerical_cols,
        "iqr_reports": iqr_reports,
        "zscore_reports": zscore_reports,
        "mad_reports": mad_reports,
        "isolation_forest": iso_report,
        "outlier_decisions": decision_results.get("outlier_decisions", []),
        "multivariate_lof": decision_results.get("multivariate_lof", {}),
        "domain_applied": decision_results.get("domain", "unspecified"),
        "objective_applied": decision_results.get("objective", "unspecified"),
    }
