"""
DataWise AI — Distribution & Normality Analysis Tool

Performs statistical testing on numerical feature distributions:
  - Normality tests:
      * Shapiro-Wilk (sample <= 5000)
      * D'Agostino's K-squared (normaltest)
  - Skewness categorization (symmetric, moderate, high)
  - Kurtosis categorization (platykurtic, mesokurtic, leptokurtic)
  - Power & logarithmic transformation recommendations:
      * log1p: strictly non-negative, right-skewed
      * Yeo-Johnson: skewed with negative values
      * Box-Cox: strictly positive skewed
      * none / standard: approximately symmetric
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd
from scipy import stats


def check_column_normality(series: pd.Series) -> Dict[str, Any]:
    """Runs statistical normality test on non-null values."""
    clean = series.dropna()
    n = len(clean)
    if n < 8:
        return {
            "test_name": "Insufficient Sample",
            "statistic": 0.0,
            "p_value": 1.0,
            "is_normal": False,
            "sample_size": n,
        }

    # Shapiro-Wilk works best for N <= 5000
    if n <= 5000:
        stat, p_val = stats.shapiro(clean)
        test_name = "Shapiro-Wilk"
    else:
        # D'Agostino-Pearson omnibus test
        stat, p_val = stats.normaltest(clean)
        test_name = "D'Agostino-Pearson Omnibus"

    stat_float = float(stat) if not np.isnan(stat) else 0.0
    p_val_float = float(p_val) if not np.isnan(p_val) else 0.0

    return {
        "test_name": test_name,
        "statistic": round(stat_float, 4),
        "p_value": round(p_val_float, 6),
        "is_normal": bool(p_val_float >= 0.05),
        "sample_size": n,
    }


def recommend_distribution_transformation(
    col: str,
    series: pd.Series,
    skewness: float,
    is_normal: bool,
) -> Dict[str, Any]:
    """Recommends mathematical transformation to stabilize variance or reduce skewness."""
    clean = series.dropna()
    min_val = float(clean.min()) if len(clean) > 0 else 0.0

    if is_normal or abs(skewness) <= 0.5:
        return {
            "recommended_transformation": "none",
            "alternative_transformations": ["standard_scaler", "minmax_scaler"],
            "rationale": f"Feature '{col}' is already approximately normally distributed (skewness = {skewness:.2f}). No non-linear transformation required.",
        }

    # Skewed features
    if skewness > 0.5:  # Right-skewed
        if min_val > 0:
            return {
                "recommended_transformation": "log",
                "alternative_transformations": ["box-cox", "yeo-johnson", "sqrt"],
                "rationale": f"Feature '{col}' is right-skewed (skewness = {skewness:.2f}) and strictly positive. Log or Box-Cox transformation will compress the upper tail.",
            }
        elif min_val == 0:
            return {
                "recommended_transformation": "log1p",
                "alternative_transformations": ["yeo-johnson", "sqrt"],
                "rationale": f"Feature '{col}' is right-skewed (skewness = {skewness:.2f}) with zeros. log1p or Yeo-Johnson will stabilize variance without undefined log(0).",
            }
        else:
            return {
                "recommended_transformation": "yeo-johnson",
                "alternative_transformations": ["quantile_transformer"],
                "rationale": f"Feature '{col}' is right-skewed with negative values (min = {min_val}). Yeo-Johnson supports negative inputs.",
            }
    else:  # Left-skewed (negative skew)
        return {
            "recommended_transformation": "yeo-johnson",
            "alternative_transformations": ["quantile_transformer"],
            "rationale": f"Feature '{col}' is left-skewed (skewness = {skewness:.2f}). Yeo-Johnson or QuantileTransformer is recommended for negative skewness.",
        }


def analyze_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """Scans all numerical features in dataframe for distribution shape and normality."""
    results: List[Dict[str, Any]] = []

    for col in df.columns:
        s = df[col]
        if not pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s) or s.nunique() <= 2:
            continue

        clean = s.dropna()
        if len(clean) < 4:
            continue

        skew_val = float(clean.skew())
        kurt_val = float(clean.kurtosis())
        normality = check_column_normality(s)

        # Skewness category
        if abs(skew_val) <= 0.5:
            skew_cat = "symmetric"
        elif abs(skew_val) <= 1.0:
            skew_cat = "moderate_skew"
        else:
            skew_cat = "high_skew"

        # Kurtosis category
        if kurt_val > 1.0:
            kurt_cat = "leptokurtic"  # heavy tails, outlier prone
        elif kurt_val < -1.0:
            kurt_cat = "platykurtic"  # light tails
        else:
            kurt_cat = "mesokurtic"   # normal-like tails

        transform_rec = recommend_distribution_transformation(
            col=str(col),
            series=s,
            skewness=skew_val,
            is_normal=normality["is_normal"],
        )

        results.append({
            "column": str(col),
            "skewness": round(skew_val, 4),
            "skewness_category": skew_cat,
            "kurtosis": round(kurt_val, 4),
            "kurtosis_category": kurt_cat,
            "normality": normality,
            "transformation_recommendation": transform_rec,
        })

    return {
        "analyzed_columns_count": len(results),
        "numerical_features": [c["column"] for c in results],
        "columns": results,
    }



class DistributionAnalyzer:
    """Class wrapper for distribution and normality analysis."""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        return analyze_distributions(df)

    def analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        return analyze_distributions(df)


def compute_distribution_metrics(series: pd.Series) -> Dict[str, Any]:
    clean = series.dropna()
    if len(clean) == 0:
        return {"mean": 0.0, "std": 0.0, "skewness": 0.0, "kurtosis": 0.0, "normality": None}
    mean_val = float(clean.mean())
    std_val = float(clean.std()) if len(clean) > 1 else 0.0
    skew_val = float(clean.skew()) if len(clean) > 2 else 0.0
    kurt_val = float(clean.kurtosis()) if len(clean) > 3 else 0.0
    normality = check_column_normality(clean)
    return {
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "skewness": round(skew_val, 4),
        "kurtosis": round(kurt_val, 4),
        "normality": normality,
    }

