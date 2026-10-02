"""
DataWise AI — Profiling: Statistical Analysis
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_column_statistics(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Calculates compact numerical and categorical summary statistics."""
    stats: Dict[str, Dict[str, Any]] = {}
    n_rows = len(df)

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isnull().sum())
        missing_pct = round((missing_count / max(n_rows, 1)) * 100, 2)
        unique_count = int(series.nunique(dropna=True))

        col_stat: Dict[str, Any] = {
            "name": col,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
        }

        if pd.api.types.is_numeric_dtype(series):
            valid = series.dropna()
            if len(valid) > 0:
                mean_val = float(valid.mean())
                std_val = float(valid.std()) if len(valid) > 1 else 0.0
                median_val = float(valid.median())
                q1 = float(valid.quantile(0.25))
                q3 = float(valid.quantile(0.75))
                iqr = q3 - q1

                col_stat.update({
                    "mean": round(mean_val, 4),
                    "std": round(std_val, 4),
                    "min": round(float(valid.min()), 4),
                    "max": round(float(valid.max()), 4),
                    "median": round(median_val, 4),
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4),
                    "zero_count": int((valid == 0).sum()),
                    "negative_count": int((valid < 0).sum()),
                    "is_constant": unique_count <= 1,
                    "is_near_constant": (unique_count > 1 and (valid.value_counts(normalize=True).iloc[0] > 0.98)),
                })
        else:
            vc = series.value_counts(dropna=True, normalize=True)
            top_val = str(vc.index[0]) if len(vc) > 0 else None
            top_freq = float(vc.iloc[0]) if len(vc) > 0 else 0.0

            col_stat.update({
                "top_value": top_val,
                "top_frequency": round(top_freq, 4),
                "is_constant": unique_count <= 1,
                "is_near_constant": top_freq > 0.98 if len(vc) > 0 else False,
            })

        stats[col] = col_stat

    return stats
