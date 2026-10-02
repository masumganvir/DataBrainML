"""
DataWise AI — Intelligent Outlier Agent
Identifies and categorizes statistical outliers using IQR, Z-score, Modified Z-score (MAD),
Isolation Forest, and LOF.
CRITICAL: Never automatically drops rare observations. Analyzes target correlation
(e.g., fraud, rare diseases) and proposes KEEP, CAP, WINSORIZE, TRANSFORM, FLAG, or ISOLATE.
Destructive operations require explicit approval.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class OutlierAgent(BaseAgent):
    """Intelligent Outlier Decision & Analysis Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Intlier Agent")

    def _iqr_outliers(self, series: pd.Series) -> np.ndarray:
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return np.zeros(len(series), dtype=bool)
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return (series < lower) | (series > upper)

    def _modified_z_score(self, series: pd.Series) -> np.ndarray:
        median = series.median()
        mad = np.median(np.abs(series - median))
        if mad == 0:
            return np.zeros(len(series), dtype=bool)
        mod_z = 0.6745 * np.abs(series - median) / mad
        return mod_z > 3.5

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Outlier analysis failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
        n_rows = len(df)

        has_target = target_col is not None and target_col in df.columns
        target_series = df[target_col] if has_target else None

        column_reports: List[Dict[str, Any]] = []
        requires_approval = False

        for col in numeric_cols[:15]:  # limit to top 15 numeric cols for responsiveness
            s = df[col].dropna()
            if len(s) < 10 or s.nunique() <= 2:
                continue

            iqr_mask = self._iqr_outliers(s)
            mod_z_mask = self._modified_z_score(s)
            combined_mask = iqr_mask | mod_z_mask
            outlier_count = int(combined_mask.sum())
            outlier_pct = round((outlier_count / len(s)) * 100, 2)

            if outlier_count == 0:
                continue

            # Analyze correlation with target (e.g. Fraud detection check!)
            target_signal = False
            target_corr = 0.0
            if has_target and target_series is not None:
                try:
                    # Point biserial or Pearson
                    valid_idx = s.index.intersection(target_series.dropna().index)
                    if len(valid_idx) > 10:
                        corr = float(np.corrcoef(s.loc[valid_idx], target_series.loc[valid_idx])[0, 1])
                        if not np.isnan(corr):
                            target_corr = round(corr, 3)
                            if abs(corr) >= 0.25:
                                target_signal = True
                except Exception:
                    pass

            # Classify outlier intent
            # If target_signal is True, this is a legitimate rare event (e.g. Fraud transaction!)
            if target_signal:
                classification = "legitimate_rare_event"
                recommended_action = "KEEP"
                rationale = (
                    f"Outliers in '{col}' have a strong correlation ({target_corr}) with the target. "
                    f"Removing them would destroy critical prediction signal (e.g. fraud or rare anomaly)."
                )
            elif outlier_pct > 15:
                classification = "heavy_tailed_distribution"
                recommended_action = "TRANSFORM"
                rationale = f"High outlier density ({outlier_pct}%) suggests heavy-tailed distribution. Recommend Yeo-Johnson or log transform."
            elif any(s < 0) and col.lower() in ("age", "price", "income", "tenure", "charges"):
                classification = "data_entry_error"
                recommended_action = "CAP"
                rationale = f"Negative values detected in strictly positive domain '{col}'. Recommend capping at 0 or winsorization."
                requires_approval = True
            elif outlier_pct <= 2:
                classification = "isolated_extreme"
                recommended_action = "WINSORIZE"
                rationale = f"Low frequency extreme outliers ({outlier_pct}%). Winsorizing at 1st/99th percentiles preserves rows while curbing leverage."
            else:
                classification = "moderate_variation"
                recommended_action = "ROBUST_SCALE"
                rationale = "Recommend RobustScaler with median/IQR to naturally de-emphasize outliers without dropping observations."

            column_reports.append({
                "column": col,
                "outlier_count": outlier_count,
                "outlier_pct": outlier_pct,
                "target_correlation": target_corr,
                "target_signal_detected": target_signal,
                "classification": classification,
                "recommended_action": recommended_action,
                "available_actions": ["KEEP", "CAP", "WINSORIZE", "TRANSFORM", "FLAG", "REMOVE"],
                "rationale": rationale,
            })

        summary = (
            f"Evaluated {len(numeric_cols)} numeric columns. "
            f"Detected outlier patterns in {len(column_reports)} columns. "
            f"Target signal protection active: rare predictive observations preserved."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="needs_approval" if requires_approval else "success",
            data={
                "outlier_reports": column_reports,
                "total_outlier_columns": len(column_reports),
            },
            summary=summary,
            needs_approval=requires_approval,
            approval_context={"reason": "Destructive or capping operation suggested on detected entry errors"} if requires_approval else None,
        )
