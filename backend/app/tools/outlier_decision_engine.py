"""
DataWise AI — Context-Aware Outlier Decision Engine

Reasons about dataset, domain, target, and ML objective to classify outliers
and recommend justifiable, explainable actions:
  - Actions: KEEP | REMOVE | CAP | WINSORIZE | TRANSFORM | INVESTIGATE
  - Classifications:
      1. data_entry_error
      2. measurement_error
      3. legitimate_rare
      4. target_signal
      5. unknown
  - Contextual awareness:
      - Fraud / Anomaly / Security -> Preserves extreme values as high-signal target instances
      - Healthcare / Vitals -> Distinguishes physiological impossibility from rare pathology
      - Unspecified domain -> Explicitly flags insufficient context and defaults to conservative retention
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.neighbors import LocalOutlierFactor

from app.state.data_science_state import OutlierDecisionItem


class OutlierDecisionEngine:
    """
    Intelligent context-driven decision engine for univariate & multivariate outliers.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        domain: Optional[str] = None,
        objective: Optional[str] = None,
    ) -> None:
        self.df = df
        self.total_rows = len(df)
        self.target_col = target_col
        self.domain = (domain or "").strip().lower()
        self.objective = (objective or "").strip().lower()

        # Identify numerical columns excluding boolean or target
        self.numerical_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_bool_dtype(df[c])
            and c != target_col
        ]

    def evaluate_outliers(self) -> Dict[str, Any]:
        """
        Runs comprehensive outlier detection across all numerical features,
        evaluates target association and domain context, and produces structured decisions.
        """
        decisions: List[OutlierDecisionItem] = []
        col_summaries: Dict[str, Any] = {}

        for col in self.numerical_cols:
            decision = self._analyze_column(col)
            if decision:
                decisions.append(decision)
                col_summaries[col] = {
                    "count": decision["outlier_count"],
                    "pct": decision["outlier_pct"],
                    "action": decision["recommended_action"],
                    "classification": decision["classified_as"],
                }

        # Multivariate evaluation using Local Outlier Factor (LOF)
        lof_summary = self._evaluate_lof()

        return {
            "total_columns_evaluated": len(self.numerical_cols),
            "columns_with_outliers": len(decisions),
            "outlier_decisions": decisions,
            "multivariate_lof": lof_summary,
            "domain_context_applied": bool(self.domain or self.objective),
            "domain": self.domain or "unspecified",
            "objective": self.objective or "unspecified",
        }

    def _analyze_column(self, col: str) -> Optional[OutlierDecisionItem]:
        s = self.df[col].dropna()
        if len(s) < 8:
            return None

        # 1. Statistical bounds calculation (IQR, MAD, Z-score)
        q1 = float(np.percentile(s, 25))
        q3 = float(np.percentile(s, 75))
        iqr = q3 - q1
        iqr_lower = q1 - 1.5 * iqr
        iqr_upper = q3 + 1.5 * iqr

        med = float(s.median())
        abs_dev = np.abs(s - med)
        mad = float(np.median(abs_dev)) or float(np.mean(abs_dev)) or 1e-6
        # Modified Z-score > 3.5
        mod_z = 0.6745 * abs_dev / mad

        std_val = float(s.std()) or 1e-6
        mean_val = float(s.mean())
        z_scores = np.abs((s - mean_val) / std_val)

        # Consensus mask (flagged by at least IQR or MAD)
        iqr_mask = (s < iqr_lower) | (s > iqr_upper)
        mad_mask = mod_z > 3.5
        z_mask = z_scores > 3.0

        combined_mask = iqr_mask | mad_mask
        outlier_indices = s[combined_mask].index.tolist()
        outlier_count = len(outlier_indices)
        outlier_pct = round((outlier_count / len(s)) * 100, 2)

        if outlier_count == 0:
            return None

        methods_triggered = []
        if iqr_mask.sum() > 0:
            methods_triggered.append("IQR (1.5x)")
        if mad_mask.sum() > 0:
            methods_triggered.append("Modified Z-Score (MAD)")
        if z_mask.sum() > 0:
            methods_triggered.append("Classic Z-Score (>3.0)")

        # 2. Maximum distance calculation
        outlier_vals = s[combined_mask]
        max_dist_ratio = 1.0
        if iqr > 0:
            dist_above = (outlier_vals.max() - q3) / iqr if outlier_vals.max() > q3 else 0.0
            dist_below = (q1 - outlier_vals.min()) / iqr if outlier_vals.min() < q1 else 0.0
            max_dist_ratio = round(float(max(dist_above, dist_below)), 2)

        # 3. Target Association Analysis
        target_assoc_note, class_assoc, is_target_predictive = self._check_target_association(col, combined_mask)

        # 4. Domain & Objective Context Reasoning
        classified_as, action, rationale, confidence = self._reason_outlier_action(
            col=col,
            series=s,
            outlier_vals=outlier_vals,
            outlier_pct=outlier_pct,
            max_dist_ratio=max_dist_ratio,
            is_target_predictive=is_target_predictive,
            target_assoc_note=target_assoc_note,
        )

        return {
            "column": col,
            "row_indices": outlier_indices[:50],  # sample row indices
            "outlier_count": outlier_count,
            "outlier_pct": outlier_pct,
            "detection_methods": methods_triggered,
            "distance_from_range": max_dist_ratio,
            "target_association": target_assoc_note,
            "class_association": class_assoc,
            "classified_as": classified_as,
            "recommended_action": action,
            "rationale": rationale,
            "confidence": confidence,
        }

    def _check_target_association(
        self, col: str, outlier_mask: pd.Series
    ) -> Tuple[Optional[str], Optional[Dict[str, float]], bool]:
        """Checks if outlier instances correlate strongly with target values or minority class."""
        if not self.target_col or self.target_col not in self.df.columns:
            return None, None, False

        target_series = self.df.loc[outlier_mask.index, self.target_col].dropna()
        if len(target_series) == 0:
            return None, None, False

        # Classification check (discrete or binary target)
        if target_series.nunique() <= 10:
            baseline_dist = (target_series.value_counts(normalize=True) * 100).round(2).to_dict()
            outlier_targets = target_series[outlier_mask]
            if len(outlier_targets) > 0:
                outlier_dist = (outlier_targets.value_counts(normalize=True) * 100).round(2).to_dict()
                class_assoc = {f"class_{k}_pct_in_outliers": v for k, v in outlier_dist.items()}

                # Check if minority class is significantly enriched in outliers
                # E.g. fraud class (1) rate in dataset is 2%, but in outliers it's 20%
                for k, v in outlier_dist.items():
                    base_v = baseline_dist.get(k, 0.0)
                    if base_v > 0 and (v / base_v) >= 2.0 and base_v < 30.0:
                        note = (
                            f"Strong target signal: Class '{k}' represents {base_v}% of the dataset "
                            f"but {v}% of the outliers (enrichment factor: {round(v / base_v, 1)}x)."
                        )
                        return note, class_assoc, True

                note = f"Outliers distributed across classes: {outlier_dist} (dataset baseline: {baseline_dist})."
                return note, class_assoc, False

        # Continuous target check (correlation)
        if pd.api.types.is_numeric_dtype(target_series):
            try:
                corr = float(self.df[col].corr(target_series))
                if abs(corr) >= 0.35:
                    note = f"Moderate/strong linear correlation with target '{self.target_col}' (r = {round(corr, 2)})."
                    return note, None, True
                return f"Weak correlation with target '{self.target_col}' (r = {round(corr, 2)}).", None, False
            except Exception:
                pass

        return None, None, False

    def _reason_outlier_action(
        self,
        col: str,
        series: pd.Series,
        outlier_vals: pd.Series,
        outlier_pct: float,
        max_dist_ratio: float,
        is_target_predictive: bool,
        target_assoc_note: Optional[str],
    ) -> Tuple[
        Literal["data_entry_error", "measurement_error", "legitimate_rare", "target_signal", "unknown"],
        Literal["KEEP", "REMOVE", "CAP", "WINSORIZE", "TRANSFORM", "INVESTIGATE"],
        str,
        Literal["HIGH", "MEDIUM", "LOW", "NEEDS_HUMAN_REVIEW"],
    ]:
        col_lower = col.lower()
        skewness = float(series.skew())

        # Rule 1: Check obvious impossible physical / data entry values
        # Age constraints
        if "age" in col_lower:
            if (outlier_vals < 0).any() or (outlier_vals > 120).any():
                return (
                    "data_entry_error",
                    "INVESTIGATE",
                    f"Column '{col}' has values outside human physiological limits (<0 or >120 years). "
                    f"Likely data entry or coding artifacts (e.g. placeholder 999). Investigate or cap to valid range.",
                    "HIGH",
                )

        # Percentage or ratio constraints (0-100% or 0-1)
        if ("pct" in col_lower or "percent" in col_lower or "rate" in col_lower) and not "amount" in col_lower:
            if (outlier_vals < 0).any() or (outlier_vals > 100).any():
                return (
                    "data_entry_error",
                    "CAP",
                    f"Percentage/rate column '{col}' contains values < 0% or > 100%. "
                    f"Capping at [0, 100] bounds prevents impossible probability or rate estimates.",
                    "HIGH",
                )

        # Strict positive metrics with negative values
        if any(w in col_lower for w in ["salary", "revenue", "price", "charge", "cost", "income", "tenure"]):
            if (outlier_vals < 0).any():
                return (
                    "data_entry_error",
                    "INVESTIGATE",
                    f"Financial/tenure column '{col}' contains negative numbers ({outlier_vals.min()}). "
                    f"Negative values in strictly positive domains indicate coding errors or unadjusted refunds.",
                    "HIGH",
                )

        # Rule 2: Fraud, Security, Anomaly Detection Objective Context
        is_fraud_or_anomaly = any(
            term in self.objective or term in self.domain
            for term in ["fraud", "anomaly", "cyber", "intrusion", "failure", "defect", "breach", "anti-money"]
        )

        if is_fraud_or_anomaly or is_target_predictive:
            # Crucial requirement: NEVER remove extreme transactions or high-signal outliers in fraud/anomaly detection!
            rationale = (
                f"Extreme values in '{col}' represent statistically rare but potentially legitimate anomaly signal. "
                f"In {self.objective or 'predictive'} modeling, removing extreme observations eliminates the exact "
                f"patterns needed to identify high-risk or minority cases. Retaining without modification preserves critical signal."
            )
            if target_assoc_note:
                rationale += f" Evidence: {target_assoc_note}"
            return ("target_signal", "KEEP", rationale, "HIGH")

        # Rule 3: Healthcare / Biomedical context
        if "healthcare" in self.domain or "medical" in self.domain or "clinical" in self.domain:
            if is_target_predictive:
                return (
                    "target_signal",
                    "KEEP",
                    f"In clinical domain, extreme measurements in '{col}' often correspond to acute pathology or clinical risk. "
                    f"Retaining these observations ensures the diagnostic model captures severe disease phenotypes.",
                    "HIGH",
                )
            if max_dist_ratio > 10.0:
                return (
                    "measurement_error",
                    "INVESTIGATE",
                    f"Extreme biomarker/clinical values in '{col}' ({max_dist_ratio}x normal range). "
                    f"Requires clinical judgment to determine if these represent assay malfunction or valid crisis states.",
                    "NEEDS_HUMAN_REVIEW",
                )

        # Rule 4: Extreme Skewness with Non-Negative Values (e.g. Income, Charges, Downloads)
        if abs(skewness) > 2.5 and (series >= 0).all():
            return (
                "legitimate_rare",
                "TRANSFORM",
                f"Column '{col}' exhibits heavy right-skew (skewness={round(skewness, 2)}). Outliers ({outlier_pct}%) "
                f"are genuine high-value tail observations. A log1p or Yeo-Johnson power transformation will compress the tail "
                f"into a normal distribution while keeping all data points intact for linear and distance-based algorithms.",
                "HIGH",
            )

        # Rule 5: Moderate Outliers with Mild Skewness
        if outlier_pct <= 3.0:
            return (
                "legitimate_rare",
                "WINSORIZE",
                f"Mild outlier concentration ({outlier_pct}% of records in '{col}'). "
                f"Winsorizing (capping at 1st and 99th percentiles) limits leverage on gradient/OLS estimators "
                f"without discarding any rows or distorting median representations.",
                "MEDIUM",
            )

        # Rule 6: Insufficient Domain Context Fallback
        if not self.domain and not self.objective:
            return (
                "unknown",
                "KEEP",
                "Domain context is insufficient to determine whether these observations are valid. "
                "I recommend keeping them until further investigation to avoid inadvertent data destruction.",
                "MEDIUM",
            )

        # Default conservative recommendation
        return (
            "legitimate_rare",
            "KEEP",
            f"Detected {outlier_pct}% extreme values in '{col}'. Retaining observations preserves natural variance. "
            f"Tree-based ensembles (Random Forest, Gradient Boosting) will be robust to these values without deletion.",
            "MEDIUM",
        )

    def _evaluate_lof(self) -> Dict[str, Any]:
        """Calculates multivariate Local Outlier Factor (LOF) when suitable."""
        if len(self.numerical_cols) < 2 or self.total_rows < 20:
            return {
                "applicable": False,
                "reason": "Requires at least 2 numerical columns and 20+ rows for multivariate LOF density estimation.",
            }

        # Subsample if dataset is very large to keep computation instantaneous
        sub_df = self.df[self.numerical_cols].dropna()
        if len(sub_df) < 15:
            return {"applicable": False, "reason": "Insufficient complete rows after dropping nulls."}

        sample_df = sub_df.sample(min(len(sub_df), 1000), random_state=42)
        try:
            lof = LocalOutlierFactor(n_neighbors=min(20, len(sample_df) - 1), contamination=0.03)
            preds = lof.fit_predict(sample_df)
            multivariate_outliers = int((preds == -1).sum())
            multivariate_pct = round((multivariate_outliers / len(sample_df)) * 100, 2)
            return {
                "applicable": True,
                "evaluated_samples": len(sample_df),
                "multivariate_outliers_detected": multivariate_outliers,
                "multivariate_outlier_pct": multivariate_pct,
                "interpretation": (
                    f"Multivariate LOF identified {multivariate_outliers} ({multivariate_pct}%) density anomalies "
                    f"across {len(self.numerical_cols)} dimensions. These records deviate from neighborhood clusters."
                    if multivariate_outliers > 0 else "Multivariate space shows coherent density clusters with no anomalous density voids."
                ),
            }
        except Exception as e:
            logger.warning(f"LOF evaluation skipped: {e}")
            return {"applicable": False, "reason": str(e)}


def analyze_outlier_decisions(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    domain: Optional[str] = None,
    objective: Optional[str] = None,
) -> Dict[str, Any]:
    """Top-level entrypoint for the Outlier Decision Engine."""
    engine = OutlierDecisionEngine(df=df, target_col=target_col, domain=domain, objective=objective)
    return engine.evaluate_outliers()
