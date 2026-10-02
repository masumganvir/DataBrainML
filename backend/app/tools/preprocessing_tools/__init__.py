"""
DataWise AI — Preprocessing Tools
Deterministic missing value analysis, outlier detection, scaling, encoding, transformations, and leakage checks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd

from app.tools.missing_value_engine import (
    MissingValueDecisionEngine,
    MissingValueDecision,
)
from app.tools.outliers import (
    OutlierAnalyzer,
    classify_outlier_severity,
)
from app.tools.outlier_decision_engine import (
    OutlierDecisionEngine,
)
from app.tools.encoding import (
    recommend_categorical_encoding,
)
from app.tools.scaling import (
    recommend_numerical_scaling,
)
from app.tools.transformation import (
    recommend_transformations,
)
from app.tools.leakage import (
    LeakageDetector,
)


def analyze_missingness(df: pd.DataFrame, is_time_series: bool = False) -> Dict[str, Any]:
    engine = MissingValueDecisionEngine(df, is_time_series=is_time_series)
    return engine.evaluate_missingness()


def recommend_imputation_strategy(df: pd.DataFrame, missing_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if missing_report is None:
        missing_report = analyze_missingness(df)
    decisions = missing_report.get("decisions", [])
    col_strategies = {d["column"]: d["recommended_strategy"] for d in decisions}
    return {
        "column_strategies": col_strategies,
        "summary": f"Formulated imputation plan for {len(col_strategies)} columns with missing data."
    }


def detect_outliers_iqr(df: pd.DataFrame) -> Dict[str, Any]:
    analyzer = OutlierAnalyzer(df)
    reports = analyzer.analyze_iqr()
    col_dict = {r["column"]: r["outlier_count"] for r in reports if r["outlier_count"] > 0}
    total_outliers = sum(col_dict.values())
    return {
        "total_unique_outlier_rows": total_outliers,
        "column_outliers": col_dict,
        "reports": reports
    }


def detect_outliers_zscore(df: pd.DataFrame) -> Dict[str, Any]:
    analyzer = OutlierAnalyzer(df)
    reports = analyzer.analyze_zscore()
    col_dict = {r["column"]: r["outlier_count"] for r in reports if r["outlier_count"] > 0}
    total_outliers = sum(col_dict.values())
    return {
        "total_unique_outlier_rows": total_outliers,
        "column_outliers": col_dict,
        "reports": reports
    }


def detect_outliers_isolation_forest(df: pd.DataFrame) -> Dict[str, Any]:
    analyzer = OutlierAnalyzer(df)
    reports = analyzer.analyze_isolation_forest()
    col_dict = {r["column"]: r["outlier_count"] for r in reports if r["outlier_count"] > 0}
    total_outliers = sum(col_dict.values())
    return {
        "total_unique_outlier_rows": total_outliers,
        "column_outliers": col_dict,
        "reports": reports
    }


def detect_outliers_lof(df: pd.DataFrame) -> Dict[str, Any]:
    return detect_outliers_isolation_forest(df)


def analyze_outlier_context(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
    engine = OutlierDecisionEngine(df, target_col=target_col)
    return engine.evaluate_outliers()


def evaluate_removal_risk(df: pd.DataFrame, outlier_res: Dict[str, Any], target_col: Optional[str] = None) -> Dict[str, Any]:
    total_outliers = outlier_res.get("total_unique_outlier_rows", 0)
    risk_level = "high" if total_outliers > len(df) * 0.1 else ("medium" if total_outliers > len(df) * 0.02 else "low")
    return {
        "risk_level": risk_level,
        "affected_rows": total_outliers,
        "recommendation": "Do not delete outliers automatically. Retain them to preserve legitimate minority signals."
    }


def suggest_encoding(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
    recs = recommend_categorical_encoding(df, target_column=target_col)
    one_hot = [r["column"] for r in recs if r.get("encoder_class") == "OneHotEncoder"]
    ordinal = [r["column"] for r in recs if r.get("encoder_class") == "OrdinalEncoder"]
    high_card = [r["column"] for r in recs if r.get("encoder_class") in ("TargetEncoder", "FrequencyEncoder")]
    return {
        "recommendations": recs,
        "one_hot_columns": one_hot,
        "ordinal_columns": ordinal,
        "high_cardinality_columns": high_card,
        "encoding_plan": recs,
    }


def suggest_scaling(df: pd.DataFrame, model_family: str = "mixed") -> Dict[str, Any]:
    recs = recommend_numerical_scaling(df, target_column=None)
    std_cols = [r["column"] for r in recs if r.get("scaler_class") == "StandardScaler"]
    minmax_cols = [r["column"] for r in recs if r.get("scaler_class") == "MinMaxScaler"]
    robust_cols = [r["column"] for r in recs if r.get("scaler_class") == "RobustScaler"]
    return {
        "recommendations": recs,
        "standard_scaled": std_cols,
        "minmax_scaled": minmax_cols,
        "robust_scaled": robust_cols,
        "scaling_plan": recs,
    }


def analyze_skewness(df: pd.DataFrame) -> Dict[str, Any]:
    recs = recommend_transformations(df)
    return {"skewed_columns": recs, "recommendations": recs}


def suggest_transformations(df: pd.DataFrame, skew_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    recs = recommend_transformations(df)
    skewed = [r["column"] for r in recs if r.get("transformer_class") not in ("none", "None")]
    return {
        "skewed_features": skewed,
        "recommendations": recs,
        "transformation_plan": recs,
    }



def detect_target_leakage(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
    if not target_col or target_col not in df.columns:
        return {"leaking_columns": [], "status": "no_target"}
    detector = LeakageDetector(df, target_column=target_col)
    res = detector.run_all()
    leaking_cols = [item["feature"] for item in res.get("leakage_flags", []) if item.get("severity") in ("CRITICAL", "HIGH")]
    return {
        "leaking_columns": leaking_cols,
        "leakage_flags": res.get("leakage_flags", []),
        "status": "leakage_detected" if leaking_cols else "clean"
    }


def check_train_test_contamination(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
    overlap = len(pd.merge(train_df, test_df, how="inner"))
    return {
        "duplicate_rows_across_splits": overlap,
        "has_contamination": overlap > 0
    }


__all__ = [
    "MissingValueDecisionEngine",
    "OutlierAnalyzer",
    "OutlierDecisionEngine",
    "LeakageDetector",
    "analyze_missingness",
    "recommend_imputation_strategy",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "detect_outliers_isolation_forest",
    "detect_outliers_lof",
    "analyze_outlier_context",
    "evaluate_removal_risk",
    "suggest_encoding",
    "suggest_scaling",
    "analyze_skewness",
    "suggest_transformations",
    "detect_target_leakage",
    "check_train_test_contamination",
]
