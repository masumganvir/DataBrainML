"""
DataWise AI — Feature Engineering Tool

Automatically generates meaningful features from the dataset:
  - Datetime decomposition (year, month, day, hour, weekday, is_weekend)
  - Ratio / interaction features between numeric pairs
  - Polynomial / squared features for skewed columns
  - Log1p transformation features
  - Text-derived features (length, word count)
  - Group-aggregation features (mean, std, count by categorical)
  - Missing-value indicator binary flags
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger


# ------------------------------------------------------------------ #
#  Feature Engineering Engine
# ------------------------------------------------------------------ #

class FeatureEngineer:
    """
    Analyses a DataFrame and returns a list of recommended feature
    engineering operations with code snippets. Nothing is applied to
    the DataFrame in-place; all operations return new frames.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
        target_col: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.df = df.copy()
        self.target_column = target_column or target_col
        self.task_type = task_type

        self.numerical_cols: List[str] = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c != target_column
        ]
        self.categorical_cols: List[str] = [
            c for c in df.select_dtypes(include=["object", "category"]).columns
            if c != target_column
        ]
        self.datetime_cols: List[str] = [
            c for c in df.columns
            if pd.api.types.is_datetime64_any_dtype(df[c]) or self._looks_like_datetime(c, df)
        ]

    # -------------------------------------------------------------- #
    #  Public API
    # -------------------------------------------------------------- #

    def recommend_features(self) -> Dict[str, Any]:
        """Return full feature engineering recommendation report."""
        plan: List[Dict[str, Any]] = []
        new_feature_names: List[str] = []
        total_new = 0

        # 1. Datetime features
        dt_ops = self._datetime_features()
        plan.extend(dt_ops)
        for op in dt_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        # 2. Ratio / Interaction features (top numeric pairs by correlation)
        ratio_ops = self._ratio_features()
        plan.extend(ratio_ops)
        for op in ratio_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        # 3. Polynomial / Squared features for skewed columns
        poly_ops = self._polynomial_features()
        plan.extend(poly_ops)
        for op in poly_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        # 4. Log1p features
        log_ops = self._log_features()
        plan.extend(log_ops)
        for op in log_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        # 5. Text features
        text_ops = self._text_features()
        plan.extend(text_ops)
        for op in text_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        # 6. Missing-value indicator flags
        indicator_ops = self._missing_indicator_features()
        plan.extend(indicator_ops)
        for op in indicator_ops:
            new_feature_names.extend(op.get("new_columns", []))
            total_new += len(op.get("new_columns", []))

        return {
            "total_new_features": total_new,
            "new_feature_names": new_feature_names,
            "operations": plan,
            "code_snippet": self._generate_code(plan),
        }

    def apply_features(self, operations: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply a list of approved operations and return augmented DataFrame."""
        result = self.df.copy()
        for op in operations:
            try:
                result = self._apply_single(result, op)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Feature op '{op.get('operation')}' failed: {exc}")
        return result

    def generate_ratio_features(self) -> List[Dict[str, Any]]:
        return self._ratio_features()

    def generate_datetime_features(self) -> List[Dict[str, Any]]:
        return self._datetime_features()

    def generate_all_recommendations(self) -> List[Dict[str, Any]]:
        return self.recommend_features().get("operations", [])

    def apply_plan(self, df: pd.DataFrame, plan: List[Dict[str, Any]]) -> pd.DataFrame:
        self.df = df.copy()
        return self.apply_features(plan)

    # -------------------------------------------------------------- #
    #  Private: operation detectors
    # -------------------------------------------------------------- #


    def _datetime_features(self) -> List[Dict[str, Any]]:
        ops = []
        for col in self.datetime_cols:
            series = pd.to_datetime(self.df[col], errors="coerce")
            new_cols = [
                f"{col}_year", f"{col}_month", f"{col}_day",
                f"{col}_dayofweek", f"{col}_is_weekend", f"{col}_quarter",
            ]
            has_time = series.dt.hour.nunique() > 1
            if has_time:
                new_cols += [f"{col}_hour", f"{col}_is_business_hour"]
            ops.append({
                "operation": "datetime_decomposition",
                "source_column": col,
                "new_columns": new_cols,
                "rationale": (
                    f"Column '{col}' contains date/time data. Decomposing into cyclical "
                    f"and ordinal components captures seasonal patterns that improve ML models."
                ),
                "impact": "HIGH",
                "requires_approval": False,
            })
        return ops

    def _ratio_features(self) -> List[Dict[str, Any]]:
        """Create ratio features for correlated or domain-meaningful numeric pairs."""
        ops = []
        if len(self.numerical_cols) < 2:
            return ops

        # Find pairs with reasonable correlation (not perfectly correlated)
        try:
            corr = self.df[self.numerical_cols].corr().abs()
            pairs: List[Tuple[str, str, float]] = []
            cols = self.numerical_cols
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    r = corr.iloc[i, j]
                    if 0.3 <= r <= 0.9:
                        pairs.append((cols[i], cols[j], float(r)))
            pairs = sorted(pairs, key=lambda x: x[2], reverse=True)[:5]

            for c1, c2, r in pairs:
                # Avoid division by zero columns
                non_zero = (self.df[c2] != 0).sum()
                if non_zero < len(self.df) * 0.9:
                    continue
                new_col = f"{c1}_div_{c2}"
                ops.append({
                    "operation": "ratio_feature",
                    "source_columns": [c1, c2],
                    "new_columns": [new_col],
                    "rationale": (
                        f"Ratio of '{c1}' to '{c2}' (correlation {r:.2f}) may encode "
                        f"proportional relationships meaningful for predictions."
                    ),
                    "impact": "MEDIUM",
                    "requires_approval": False,
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Ratio feature extraction failed: {exc}")
        return ops

    def _polynomial_features(self) -> List[Dict[str, Any]]:
        """Add squared terms for numerically skewed features."""
        ops = []
        for col in self.numerical_cols:
            try:
                skew = float(self.df[col].skew())
            except Exception:  # noqa: BLE001
                continue
            if abs(skew) > 1.5 and self.df[col].min() >= 0:
                new_col = f"{col}_squared"
                ops.append({
                    "operation": "polynomial_feature",
                    "source_column": col,
                    "degree": 2,
                    "new_columns": [new_col],
                    "rationale": (
                        f"Column '{col}' is highly skewed (skewness={skew:.2f}). "
                        f"Adding a squared term allows linear models to capture non-linear relationships."
                    ),
                    "impact": "MEDIUM",
                    "requires_approval": False,
                })
        return ops[:4]  # Limit to top 4

    def _log_features(self) -> List[Dict[str, Any]]:
        """Recommend log1p features for positive, right-skewed numerics."""
        ops = []
        for col in self.numerical_cols:
            try:
                skew = float(self.df[col].skew())
                min_val = float(self.df[col].min())
            except Exception:  # noqa: BLE001
                continue
            if skew > 2.0 and min_val >= 0:
                new_col = f"{col}_log1p"
                ops.append({
                    "operation": "log1p_feature",
                    "source_column": col,
                    "new_columns": [new_col],
                    "rationale": (
                        f"Column '{col}' is right-skewed (skewness={skew:.2f}) with non-negative values. "
                        f"log1p transformation normalizes the distribution for distance-based models."
                    ),
                    "impact": "HIGH",
                    "requires_approval": False,
                })
        return ops[:4]

    def _text_features(self) -> List[Dict[str, Any]]:
        """Extract length and word-count features from object columns with long text."""
        ops = []
        for col in self.categorical_cols:
            try:
                avg_len = self.df[col].dropna().astype(str).str.len().mean()
                if avg_len > 30:
                    ops.append({
                        "operation": "text_features",
                        "source_column": col,
                        "new_columns": [f"{col}_char_count", f"{col}_word_count"],
                        "rationale": (
                            f"Column '{col}' contains long text (avg {avg_len:.0f} chars). "
                            f"Character count and word count are lightweight NLP proxies."
                        ),
                        "impact": "LOW",
                        "requires_approval": False,
                    })
            except Exception:  # noqa: BLE001
                continue
        return ops

    def _missing_indicator_features(self) -> List[Dict[str, Any]]:
        """Create binary indicator columns for columns with notable missingness."""
        ops = []
        for col in self.df.columns:
            if col == self.target_column:
                continue
            missing_pct = self.df[col].isna().mean() * 100
            if 5.0 <= missing_pct <= 70.0:
                new_col = f"{col}_is_missing"
                ops.append({
                    "operation": "missing_indicator",
                    "source_column": col,
                    "new_columns": [new_col],
                    "rationale": (
                        f"Column '{col}' has {missing_pct:.1f}% missing values. "
                        f"A binary indicator preserves the information that data was absent, "
                        f"which can itself be predictive."
                    ),
                    "impact": "MEDIUM",
                    "requires_approval": False,
                })
        return ops

    # -------------------------------------------------------------- #
    #  Private: apply individual operations
    # -------------------------------------------------------------- #

    def _apply_single(self, df: pd.DataFrame, op: Dict[str, Any]) -> pd.DataFrame:
        kind = op["operation"]
        if kind == "datetime_decomposition":
            col = op["source_column"]
            series = pd.to_datetime(df[col], errors="coerce")
            df[f"{col}_year"] = series.dt.year
            df[f"{col}_month"] = series.dt.month
            df[f"{col}_day"] = series.dt.day
            df[f"{col}_dayofweek"] = series.dt.dayofweek
            df[f"{col}_is_weekend"] = series.dt.dayofweek.isin([5, 6]).astype(int)
            df[f"{col}_quarter"] = series.dt.quarter
            if f"{col}_hour" in op.get("new_columns", []):
                df[f"{col}_hour"] = series.dt.hour
                df[f"{col}_is_business_hour"] = series.dt.hour.between(9, 17).astype(int)
        elif kind == "ratio_feature":
            c1, c2 = op["source_columns"]
            df[op["new_columns"][0]] = df[c1] / df[c2].replace(0, np.nan)
        elif kind == "polynomial_feature":
            col = op["source_column"]
            df[op["new_columns"][0]] = df[col] ** op.get("degree", 2)
        elif kind == "log1p_feature":
            col = op["source_column"]
            df[op["new_columns"][0]] = np.log1p(df[col].clip(lower=0))
        elif kind == "text_features":
            col = op["source_column"]
            s = df[col].fillna("").astype(str)
            df[f"{col}_char_count"] = s.str.len()
            df[f"{col}_word_count"] = s.str.split().str.len()
        elif kind == "missing_indicator":
            col = op["source_column"]
            df[op["new_columns"][0]] = df[col].isna().astype(int)
        return df

    # -------------------------------------------------------------- #
    #  Private: helpers
    # -------------------------------------------------------------- #

    @staticmethod
    def _looks_like_datetime(col_name: str, df: pd.DataFrame) -> bool:
        """Heuristic: column name contains date/time keywords and is string type."""
        pattern = re.compile(r"(date|time|timestamp|created|updated|dt)$", re.IGNORECASE)
        if not pattern.search(col_name):
            return False
        sample = df[col_name].dropna().head(5).astype(str)
        try:
            pd.to_datetime(sample, infer_datetime_format=True)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _generate_code(self, operations: List[Dict[str, Any]]) -> str:
        lines = [
            "# ── Auto-generated Feature Engineering Code ──",
            "import numpy as np",
            "import pandas as pd",
            "",
            "# Assumes `df` is the working DataFrame",
            "",
        ]
        for op in operations:
            kind = op["operation"]
            if kind == "datetime_decomposition":
                col = op["source_column"]
                lines += [
                    f"# Datetime decomposition: {col}",
                    f"_dt_{col} = pd.to_datetime(df['{col}'], errors='coerce')",
                    f"df['{col}_year']      = _dt_{col}.dt.year",
                    f"df['{col}_month']     = _dt_{col}.dt.month",
                    f"df['{col}_day']       = _dt_{col}.dt.day",
                    f"df['{col}_dayofweek'] = _dt_{col}.dt.dayofweek",
                    f"df['{col}_is_weekend']= _dt_{col}.dt.dayofweek.isin([5,6]).astype(int)",
                    f"df['{col}_quarter']   = _dt_{col}.dt.quarter",
                    "",
                ]
            elif kind == "ratio_feature":
                c1, c2 = op["source_columns"]
                new = op["new_columns"][0]
                lines.append(f"df['{new}'] = df['{c1}'] / df['{c2}'].replace(0, np.nan)")
            elif kind == "polynomial_feature":
                col = op["source_column"]
                new = op["new_columns"][0]
                deg = op.get("degree", 2)
                lines.append(f"df['{new}'] = df['{col}'] ** {deg}")
            elif kind == "log1p_feature":
                col = op["source_column"]
                new = op["new_columns"][0]
                lines.append(f"df['{new}'] = np.log1p(df['{col}'].clip(lower=0))")
            elif kind == "text_features":
                col = op["source_column"]
                lines += [
                    f"_s_{col} = df['{col}'].fillna('').astype(str)",
                    f"df['{col}_char_count'] = _s_{col}.str.len()",
                    f"df['{col}_word_count'] = _s_{col}.str.split().str.len()",
                ]
            elif kind == "missing_indicator":
                col = op["source_column"]
                new = op["new_columns"][0]
        return "\n".join(lines)

    def apply_plan(self, df: pd.DataFrame, operations: List[Dict[str, Any]]) -> pd.DataFrame:
        """Applies feature engineering operations to df and returns the augmented frame."""
        res = df.copy()
        for op in operations:
            kind = op.get("operation")
            if kind == "datetime_decomposition":
                col = op["source_column"]
                dt = pd.to_datetime(res[col], errors="coerce")
                res[f"{col}_year"] = dt.dt.year
                res[f"{col}_month"] = dt.dt.month
                res[f"{col}_day"] = dt.dt.day
                res[f"{col}_dayofweek"] = dt.dt.dayofweek
                res[f"{col}_is_weekend"] = dt.dt.dayofweek.isin([5, 6]).astype(int)
                res[f"{col}_quarter"] = dt.dt.quarter
            elif kind == "ratio_feature":
                c1, c2 = op["source_columns"]
                new = op["new_columns"][0]
                denom = res[c2].replace(0, np.nan)
                res[new] = res[c1] / denom
            elif kind == "polynomial_feature":
                col = op["source_column"]
                new = op["new_columns"][0]
                deg = op.get("degree", 2)
                res[new] = res[col] ** deg
            elif kind == "log1p_feature":
                col = op["source_column"]
                new = op["new_columns"][0]
                res[new] = np.log1p(res[col].clip(lower=0))
            elif kind == "text_features":
                col = op["source_column"]
                s = res[col].fillna("").astype(str)
                res[f"{col}_char_count"] = s.str.len()
                res[f"{col}_word_count"] = s.str.split().str.len()
            elif kind == "missing_indicator":
                col = op["source_column"]
                new = op["new_columns"][0]
                res[new] = res[col].isna().astype(int)
        return res

    # -------------------------------------------------------------- #
    #  Static factory
    # -------------------------------------------------------------- #

    @classmethod
    def from_path(
        cls,
        file_path: str,
        target_column: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> "FeatureEngineer":
        ext = file_path.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            df = pd.read_csv(file_path)
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
        elif ext == "json":
            df = pd.read_json(file_path)
        else:
            df = pd.read_csv(file_path)
        return cls(df, target_column=target_column, task_type=task_type)
