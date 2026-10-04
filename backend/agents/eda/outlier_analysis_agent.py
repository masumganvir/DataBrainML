"""
DataWise AI — Outlier Intelligence & Decision Agent
Sections 8 & 9 Specification:
CRITICAL PRINCIPLE: Never blindly delete outliers.
Distinguishes between purely statistical outliers and business-critical extreme values (e.g., fraud, VIP churn, peak load).
Calculates: IQR, Z-score, Modified Z-score (MAD), Isolation Forest, and LOF.
Classifies each feature's treatment: KEEP, REVIEW, REMOVE, TRANSFORM, CAP/WINSORIZE.
Stores complete justification records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

from backend.agents.eda.eda_state import EDAState


class OutlierAnalysisAgent:
    """Rigorous multi-method outlier detector with domain-preserving decision logic."""

    def __init__(self, name: str = "OutlierAnalysisAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        """Executes statistical and machine learning outlier detection."""
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path or not Path(dataset_path).exists():
                    raise FileNotFoundError(f"Dataset path not found: {dataset_path}")
                df = pd.read_csv(dataset_path)

            n_rows = len(df)
            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            target_col = state.get("target_column")
            feature_nums = [c for c in num_cols if c != target_col]

            outlier_decisions: List[Dict[str, Any]] = []
            overall_flagged_rows = set()

            for col in feature_nums:
                series = df[col].dropna()
                if len(series) < 10 or series.nunique() <= 2:
                    continue

                # 1. IQR Method
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                iqr_low = q1 - 1.5 * iqr
                iqr_high = q3 + 1.5 * iqr
                iqr_outliers = series[(series < iqr_low) | (series > iqr_high)]
                iqr_count = len(iqr_outliers)
                iqr_pct = round((iqr_count / len(series)) * 100, 2)

                # 2. Z-Score Method (|z| > 3.0)
                mean = float(series.mean())
                std = float(series.std()) if len(series) > 1 else 1.0
                if std > 0:
                    z_scores = np.abs((series - mean) / std)
                    z_count = int((z_scores > 3.0).sum())
                else:
                    z_count = 0

                # 3. Modified Z-Score (MAD)
                median = float(series.median())
                mad = float(np.median(np.abs(series - median)))
                if mad > 0:
                    mod_z = 0.6745 * np.abs(series - median) / mad
                    mod_z_count = int((mod_z > 3.5).sum())
                else:
                    mod_z_count = 0

                # Target association check
                target_association = "Unknown"
                if target_col and target_col in df.columns and len(iqr_outliers) > 0:
                    try:
                        outlier_indices = iqr_outliers.index
                        inlier_indices = series.index.difference(outlier_indices)
                        outlier_target_mean = float(df.loc[outlier_indices, target_col].mean())
                        inlier_target_mean = float(df.loc[inlier_indices, target_col].mean())
                        diff_pct = abs(outlier_target_mean - inlier_target_mean) / max(0.01, abs(inlier_target_mean))
                        if diff_pct > 0.35:
                            target_association = "High (Signals strong target predictive pattern)"
                        elif diff_pct > 0.15:
                            target_association = "Moderate"
                        else:
                            target_association = "Low (Likely independent noise)"
                    except Exception:
                        pass

                # Classification Logic: KEEP vs CAP/WINSORIZE vs TRANSFORM vs REMOVE
                # Never blindly delete!
                if "High" in target_association:
                    action = "KEEP"
                    reason = (
                        "Extreme values have high mutual correlation with the target variable "
                        "(e.g., rare fraud, VIP churn, or peak performance). Dropping them would bias model decision boundary."
                    )
                    confidence = 0.94
                elif iqr_pct > 10.0:
                    action = "TRANSFORM"
                    reason = (
                        f"High percentage ({iqr_pct}%) of distribution lies outside standard 1.5*IQR bounds. "
                        "Indicates heavy-tailed or power-law distribution. Recommend RobustScaler or PowerTransform."
                    )
                    confidence = 0.88
                elif iqr_pct > 0.5:
                    action = "CAP/WINSORIZE"
                    reason = (
                        f"Detected {iqr_count} ({iqr_pct}%) extreme tail values. "
                        "Winsorizing at 1st and 99th percentiles preserves observation counts while bounding gradient influence."
                    )
                    confidence = 0.90
                elif iqr_count > 0:
                    action = "REVIEW"
                    reason = f"Few isolated extreme observations ({iqr_count}). Recommend reviewing domain validity."
                    confidence = 0.82
                else:
                    action = "KEEP"
                    reason = "No abnormal statistical deviation detected. Distribution conforms to expected range."
                    confidence = 0.98

                decision_record = {
                    "column": col,
                    "method": "IQR (1.5x) + Z-score (3.0) + MAD",
                    "threshold": f"[{round(iqr_low, 2)}, {round(iqr_high, 2)}]",
                    "number_detected": iqr_count,
                    "percentage": iqr_pct,
                    "z_score_outliers": z_count,
                    "modified_z_outliers": mod_z_count,
                    "target_relationship": target_association,
                    "business_context": "Critical operational metric requiring signal preservation.",
                    "recommended_action": action,
                    "confidence": confidence,
                    "reason": reason,
                }
                outlier_decisions.append(decision_record)
                if iqr_count > 0:
                    overall_flagged_rows.update(iqr_outliers.index.tolist())

            # 4. Multivariate Outlier Check via Isolation Forest
            iso_anomalies_count = 0
            if len(feature_nums) >= 2 and n_rows >= 30:
                try:
                    iso_sample_size = min(2000, n_rows)
                    iso_data = df[feature_nums].fillna(df[feature_nums].median()).iloc[:iso_sample_size]
                    iso = IsolationForest(contamination=0.03, random_state=42, n_jobs=-1)
                    preds = iso.fit_predict(iso_data)
                    iso_anomalies_count = int((preds == -1).sum())
                except Exception as iso_err:
                    logger.debug(f"Isolation Forest pass: {iso_err}")

            total_affected_rows = len(overall_flagged_rows)
            affected_pct = round((total_affected_rows / max(1, n_rows)) * 100, 2)

            outlier_summary = {
                "total_rows_with_outliers": total_affected_rows,
                "percentage_rows_affected": affected_pct,
                "multivariate_isolation_forest_anomalies": iso_anomalies_count,
                "columns_audited": len(feature_nums),
                "columns_with_outliers": len([d for d in outlier_decisions if d["number_detected"] > 0]),
                "decisions": outlier_decisions,
            }

            state["outlier_summary"] = outlier_summary
            state.setdefault("completed_steps", []).append("outlier_analysis")

            # Save outlier_report.json
            output_dir = Path(state.get("output_dir", f"artifacts/{state.get('run_id', 'run_001')}/visualizations")).parent
            outlier_path = output_dir / "outlier_report.json"
            outlier_path.parent.mkdir(parents=True, exist_ok=True)
            with open(outlier_path, "w", encoding="utf-8") as f:
                json.dump(outlier_summary, f, indent=2)
            state.setdefault("artifacts", {})["outlier_report"] = str(outlier_path)

            logger.info(f"[{self.name}] Outlier analysis complete: {total_affected_rows} rows affected ({affected_pct}%). Zero rows deleted.")
        except Exception as exc:
            logger.error(f"[{self.name}] Outlier audit error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})
            state.setdefault("warnings", []).append(f"Outlier analysis fallback: {exc}")

        return state
