"""
DataWise AI — Bivariate EDA Agent
Section 11 Specification:
Explores pairwise feature interactions:
- Numerical vs Numerical: Scatter, Regression, Hexbin (large data), Pearson & Spearman
- Categorical vs Numerical: Box Plot, Violin Plot, Grouped Bar
- Categorical vs Categorical: Stacked Bar, Cross-tabulation, Cramér's V
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from scipy import stats

from backend.agents.eda.eda_state import EDAState


def _cramers_v(confusion_matrix: pd.DataFrame) -> float:
    """Calculates Cramér's V statistic for categorical-categorical association."""
    try:
        chi2 = stats.chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2 / max(1, n)
        r, k = confusion_matrix.shape
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        rcorr = r - ((r - 1) ** 2) / (n - 1)
        kcorr = k - ((k - 1) ** 2) / (n - 1)
        denom = min((kcorr - 1), (rcorr - 1))
        if denom <= 0:
            return 0.0
        return round(float(np.sqrt(phi2corr / denom)), 4)
    except Exception:
        return 0.0


class BivariateEDAAgent:
    """Computes targeted bivariate statistics and identifies strongest feature associations."""

    def __init__(self, name: str = "BivariateEDAAgent"):
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
            target_col = state.get("target_column")

            top_num_pairs: List[Dict[str, Any]] = []
            # Calculate top numerical-numerical correlations
            for i in range(min(10, len(num_cols))):
                for j in range(i + 1, min(10, len(num_cols))):
                    c1, c2 = num_cols[i], num_cols[j]
                    valid = df[[c1, c2]].dropna()
                    if len(valid) > 10:
                        corr_val = float(valid[c1].corr(valid[c2]))
                        if abs(corr_val) > 0.25:
                            top_num_pairs.append({
                                "col1": c1,
                                "col2": c2,
                                "pearson": round(corr_val, 4),
                                "recommended_plot": "hexbin" if len(valid) > 5000 else "scatter",
                            })

            top_num_pairs.sort(key=lambda x: abs(x["pearson"]), reverse=True)

            # Categorical vs Numerical (Group stats)
            cat_num_pairs: List[Dict[str, Any]] = []
            for c_cat in cat_cols[:4]:
                if df[c_cat].nunique() < 2 or df[c_cat].nunique() > 10:
                    continue
                for c_num in num_cols[:4]:
                    try:
                        grp = df.groupby(c_cat)[c_num].mean().dropna().to_dict()
                        cat_num_pairs.append({
                            "categorical": c_cat,
                            "numerical": c_num,
                            "group_means": {str(k): round(float(v), 2) for k, v in grp.items()},
                            "recommended_plot": "boxplot",
                        })
                    except Exception:
                        pass

            bivariate_results = {
                "top_numerical_pairs": top_num_pairs[:8],
                "categorical_numerical_pairs": cat_num_pairs[:6],
            }

            state.setdefault("eda_results", {})["bivariate"] = bivariate_results
            state.setdefault("completed_steps", []).append("bivariate_eda")
            logger.info(f"[{self.name}] Identified {len(top_num_pairs)} strong continuous associations.")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in bivariate EDA: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
