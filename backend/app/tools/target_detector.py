"""
DataWise AI — Target Column Detection & ML Task Classifier

Automatically:
  1. Scores every column as a target candidate
  2. Ranks candidates by likelihood
  3. Infers ML task type (classification / regression / clustering / time_series)
  4. Analyses class distribution and imbalance for classification tasks
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger


# ------------------------------------------------------------------ #
#  Task type thresholds
# ------------------------------------------------------------------ #

CLASSIFICATION_UNIQUE_RATIO_MAX = 0.05   # unique / row count ≤ 5%
CLASSIFICATION_MAX_UNIQUE_ABSOLUTE = 30  # hard limit
REGRESSION_MIN_UNIQUE_RATIO = 0.02      # at least 2% unique for numeric target
IMBALANCE_RATIO_THRESHOLD = 3.0         # majority:minority ≥ 3 → imbalanced


class TargetDetector:
    """
    Scores every column for likelihood of being the ML target, then
    determines the most probable ML task type.
    """

    def __init__(self, df: Optional[pd.DataFrame] = None) -> None:
        self.df = df

    # -------------------------------------------------------------- #
    #  Public API
    # -------------------------------------------------------------- #

    def detect(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        target_df = df if df is not None else self.df
        if target_df is None:
            raise ValueError("No DataFrame provided to TargetDetector.")
        self.df = target_df

        candidates = []
        for col in self.df.columns:
            score, rationale = self._score_column(col)
            candidates.append({
                "column": col,
                "score": round(score, 3),
                "rationale": rationale,
                "inferred_task": self._infer_task_for_column(col),
            })

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        top = candidates[0] if candidates else None

        result: Dict[str, Any] = {
            "candidates": candidates[:10],  # top 10 candidates
            "recommended_target": top["column"] if top else None,
            "primary_candidate": top["column"] if top else None,
            "recommended_task": top["inferred_task"] if top else "classification",
            "task_type": top["inferred_task"] if top else "classification",
            "confidence": top["score"] if top else 0.0,
        }

        if top:
            result["class_analysis"] = self._class_analysis(
                top["column"], top["inferred_task"]
            )

        return result

    def detect_target_candidates(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Convenience alias for detect() providing primary_candidate and task_type."""
        return self.detect(df)

    def analyse_target(
        self, target_column: str, task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Given a confirmed target column, analyse it in detail."""
        if target_column not in self.df.columns:
            return {"error": f"Column '{target_column}' not found."}

        inferred = task_type or self._infer_task_for_column(target_column)
        return {
            "target_column": target_column,
            "task_type": inferred,
            "class_analysis": self._class_analysis(target_column, inferred),
        }

    analyze_target = analyse_target
    analyze_target_characteristics = analyse_target

    # -------------------------------------------------------------- #
    #  Private: scoring
    # -------------------------------------------------------------- #


    def _score_column(self, col: str) -> tuple[float, str]:
        """Return (0–1 score, rationale string) for a single column."""
        score = 0.0
        notes: List[str] = []
        series = self.df[col]
        n = len(series)
        n_unique = series.nunique()
        unique_ratio = n_unique / n if n > 0 else 0

        # ── Name heuristics ──────────────────────────────────────────
        name_lower = col.lower()
        if any(kw in name_lower for kw in ("target", "label", "class", "y", "output", "result")):
            score += 0.5
            notes.append("Column name suggests target variable")
        if any(kw in name_lower for kw in ("id", "uuid", "key", "index", "code")):
            score -= 0.4
            notes.append("Column name suggests identifier")
        if any(kw in name_lower for kw in ("date", "time", "timestamp", "created", "updated")):
            score -= 0.3
            notes.append("Column name suggests timestamp")

        # ── Position heuristic (last column often the target) ────────
        if list(self.df.columns).index(col) == len(self.df.columns) - 1:
            score += 0.15
            notes.append("Last column (common convention for target)")

        # ── Dtype heuristics ─────────────────────────────────────────
        if pd.api.types.is_bool_dtype(series):
            score += 0.3
            notes.append("Boolean type — likely binary classification target")

        elif series.dtype == object or str(series.dtype) == "category":
            if n_unique <= CLASSIFICATION_MAX_UNIQUE_ABSOLUTE and unique_ratio <= CLASSIFICATION_UNIQUE_RATIO_MAX:
                score += 0.25
                notes.append(f"Categorical with {n_unique} classes — suitable classification target")
            elif n_unique > 100:
                score -= 0.3
                notes.append("High-cardinality categorical — unlikely target")

        elif pd.api.types.is_numeric_dtype(series):
            if n_unique <= CLASSIFICATION_MAX_UNIQUE_ABSOLUTE and unique_ratio <= CLASSIFICATION_UNIQUE_RATIO_MAX:
                score += 0.2
                notes.append(f"Numeric with only {n_unique} unique values — likely discrete target")
            elif unique_ratio >= REGRESSION_MIN_UNIQUE_RATIO:
                score += 0.1
                notes.append("Continuous numeric — plausible regression target")

        # ── Missing values penalty ───────────────────────────────────
        missing_pct = series.isna().mean()
        if missing_pct > 0.05:
            score -= 0.2
            notes.append(f"High missingness ({missing_pct*100:.1f}%) — targets rarely have missing values")

        return max(0.0, min(1.0, score)), "; ".join(notes) if notes else "No special signals"

    def _infer_task_for_column(self, col: str) -> str:
        series = self.df[col].dropna()
        n = len(series)
        n_unique = series.nunique()

        # Time series detection
        if pd.api.types.is_datetime64_any_dtype(series):
            return "time_series"

        # Binary classification
        if n_unique == 2:
            return "classification"

        # Multi-class (discrete numeric or categorical)
        if series.dtype == object or str(series.dtype) == "category":
            return "classification"

        # Numeric with few unique values → classification
        if pd.api.types.is_numeric_dtype(series):
            if n_unique <= CLASSIFICATION_MAX_UNIQUE_ABSOLUTE and (n_unique / n) <= CLASSIFICATION_UNIQUE_RATIO_MAX:
                return "classification"
            return "regression"

        return "clustering"

    # -------------------------------------------------------------- #
    #  Private: class analysis
    # -------------------------------------------------------------- #

    def _class_analysis(self, target_column: str, task_type: str) -> Dict[str, Any]:
        series = self.df[target_column].dropna()

        if task_type == "regression":
            return {
                "task_type": "regression",
                "statistics": {
                    "mean": float(series.mean()) if pd.api.types.is_numeric_dtype(series) else None,
                    "std": float(series.std()) if pd.api.types.is_numeric_dtype(series) else None,
                    "min": float(series.min()) if pd.api.types.is_numeric_dtype(series) else None,
                    "max": float(series.max()) if pd.api.types.is_numeric_dtype(series) else None,
                    "skewness": float(series.skew()) if pd.api.types.is_numeric_dtype(series) else None,
                },
                "is_imbalanced": False,
                "imbalance_ratio": None,
                "imbalance_severity": "N/A",
                "imbalance_recommendation": None,
                "recommended_metrics": ["rmse", "mae", "r2"],
                "production_criteria": ["performance", "robustness", "latency", "memory", "interpretability"],
            }

        # Classification analysis
        dist = series.value_counts()
        class_distribution = {str(k): int(v) for k, v in dist.items()}
        majority = int(dist.iloc[0]) if len(dist) > 0 else 1
        minority = int(dist.iloc[-1]) if len(dist) > 1 else majority
        imbalance_ratio = majority / minority if minority > 0 else 1.0

        is_imbalanced = imbalance_ratio >= IMBALANCE_RATIO_THRESHOLD
        is_fraud = "fraud" in target_column.lower() or imbalance_ratio >= 20.0

        if is_fraud or imbalance_ratio >= 20.0:
            severity = "Extreme Imbalance (Fraud Pattern)"
            recommendation = "Use PR-AUC + Recall + Precision + threshold analysis. Never optimize raw accuracy."
            recommended_metrics = ["pr_auc", "recall", "precision", "threshold_analysis"]
        elif imbalance_ratio < IMBALANCE_RATIO_THRESHOLD:
            severity = "Balanced"
            recommendation = "Dataset is well-balanced. Standard binary classification metrics apply."
            recommended_metrics = ["f1", "roc_auc", "accuracy"]
        elif imbalance_ratio < 10:
            severity = "Moderate Imbalance"
            recommendation = "Use class_weight='balanced' or SMOTE to address moderate imbalance."
            recommended_metrics = ["f1", "roc_auc", "balanced_accuracy"]
        else:
            severity = "Severe Imbalance"
            recommendation = "Apply SMOTE or cost-sensitive learning. Use PR-AUC/F1 over accuracy."
            recommended_metrics = ["pr_auc", "f1", "recall", "precision"]

        return {
            "task_type": "classification",
            "num_classes": len(dist),
            "class_distribution": class_distribution,
            "majority_class": str(dist.index[0]) if len(dist) > 0 else None,
            "minority_class": str(dist.index[-1]) if len(dist) > 1 else None,
            "majority_count": majority,
            "minority_count": minority,
            "imbalance_ratio": round(imbalance_ratio, 2),
            "is_imbalanced": is_imbalanced,
            "is_fraud_pattern": is_fraud,
            "imbalance_severity": severity,
            "imbalance_recommendation": recommendation,
            "recommended_metrics": recommended_metrics,
            "production_criteria": ["performance", "robustness", "latency", "memory", "interpretability"],
        }


def detect_target_column(df: pd.DataFrame) -> Dict[str, Any]:
    detector = TargetDetector(df)
    return detector.detect()


def classify_problem_type(df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, Any]:
    detector = TargetDetector(df)
    if target_column and target_column in df.columns:
        analysis = detector.analyse_target(target_column)
        task_type = analysis.get("task_type", "classification")
        class_info = analysis.get("class_analysis", {})
        return {
            "target_column": target_column,
            "problem_type": task_type,
            "task_type": task_type,
            "class_analysis": class_info,
            "rationale": f"Target '{target_column}' formulated as {task_type}.",
            "recommended_metrics": ["accuracy", "f1", "roc_auc"] if "class" in task_type else ["rmse", "mae", "r2"]
        }
    res = detector.detect()
    top_target = res.get("recommended_target")
    if top_target:
        return classify_problem_type(df, top_target)
    return {"problem_type": "clustering", "task_type": "clustering", "recommended_metrics": ["silhouette_score"]}



