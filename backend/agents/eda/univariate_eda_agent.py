"""
DataWise AI — Univariate EDA Agent
Section 10 Specification:
Analyzes individual features in isolation:
- Numerical: Histogram, KDE, Box Plot, Violin Plot, ECDF, QQ Plot, summary stats
- Categorical: Count Plot, Frequency Table, Top-N categories
- Datetime: Time distribution, trend line, frequency over time
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from scipy import stats

from backend.agents.eda.eda_state import EDAState


class UnivariateEDAAgent:
    """Computes detailed univariate statistical profiles for all features."""

    def __init__(self, name: str = "UnivariateEDAAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            cat_cols = state.get("categorical_columns") or list(df.select_dtypes(exclude=[np.number]).columns)
            dt_cols = state.get("datetime_columns") or []

            num_profiles: Dict[str, Any] = {}
            for col in num_cols:
                series = df[col].dropna()
                if series.empty:
                    continue

                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1

                # Quantile-Quantile & Normality check
                shapiro_p = None
                if len(series) >= 8:
                    sample = series.sample(min(500, len(series)), random_state=42)
                    try:
                        _, shapiro_p = stats.shapiro(sample)
                        shapiro_p = round(float(shapiro_p), 5)
                    except Exception:
                        pass

                num_profiles[col] = {
                    "count": int(len(series)),
                    "mean": round(float(series.mean()), 4),
                    "std": round(float(series.std()), 4) if len(series) > 1 else 0.0,
                    "median": round(float(series.median()), 4),
                    "iqr": round(float(iqr), 4),
                    "min": round(float(series.min()), 4),
                    "max": round(float(series.max()), 4),
                    "skewness": round(float(series.skew()), 4) if len(series) > 2 else 0.0,
                    "kurtosis": round(float(series.kurtosis()), 4) if len(series) > 3 else 0.0,
                    "normality_p_value": shapiro_p,
                    "is_normal": (shapiro_p is not None and shapiro_p > 0.05),
                    "recommended_plots": ["histogram", "kde", "boxplot", "ecdf"],
                }

            cat_profiles: Dict[str, Any] = {}
            for col in cat_cols:
                series = df[col].dropna()
                if series.empty:
                    continue

                val_counts = series.value_counts()
                top_5 = val_counts.head(5).to_dict()
                cat_profiles[col] = {
                    "cardinality": int(series.nunique()),
                    "top_categories": {str(k): int(v) for k, v in top_5.items()},
                    "top_category_pct": round(float(val_counts.iloc[0] / len(series)) * 100, 2) if not val_counts.empty else 0.0,
                    "recommended_plots": ["barplot", "countplot", "frequency_table"],
                }

            univariate_results = {
                "numerical": num_profiles,
                "categorical": cat_profiles,
                "datetime_columns": dt_cols,
            }

            state.setdefault("eda_results", {})["univariate"] = univariate_results
            state.setdefault("completed_steps", []).append("univariate_eda")
            logger.info(f"[{self.name}] Profiled {len(num_profiles)} numeric and {len(cat_profiles)} categorical features.")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in univariate EDA: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
