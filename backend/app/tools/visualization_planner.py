"""
DataWise AI — Visualization Planner & Selection Engine

Selects the most informative visualizations based on:
  - Dataset metadata & size
  - Feature distributions and cardinality
  - Analytical findings (outliers, skewness, missingness)
  - ML task (Classification, Regression, Clustering, Time-Series)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd


class VisualizationPlanItem:
    def __init__(
        self,
        plot_type: str,
        feature: Optional[str],
        reason: str,
        priority: Literal["high", "medium", "low"],
        category: str,
        target_feature: Optional[str] = None,
    ) -> None:
        self.plot_type = plot_type
        self.feature = feature
        self.reason = reason
        self.priority = priority
        self.category = category
        self.target_feature = target_feature

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plot_type": self.plot_type,
            "feature": self.feature,
            "target_feature": self.target_feature,
            "reason": self.reason,
            "priority": self.priority,
            "category": self.category,
        }


class VisualizationPlanner:
    """
    Intelligent planner that creates a curated visual inspection strategy.
    Does NOT generate every possible plot; prioritizes high-signal visualizations.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        task_type: Optional[str] = None,
        outlier_reports: Optional[List[Dict[str, Any]]] = None,
        distribution_reports: Optional[Dict[str, Any]] = None,
        missing_reports: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.df = df
        self.total_rows = len(df)
        self.target_col = target_col
        self.task_type = task_type
        self.outlier_reports = outlier_reports or []
        self.distribution_reports = distribution_reports or {}
        self.missing_reports = missing_reports or []

        self.num_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
        ]
        self.cat_cols = [
            str(c) for c in df.columns
            if pd.api.types.is_object_dtype(df[c])
            or pd.api.types.is_categorical_dtype(df[c])
            or pd.api.types.is_bool_dtype(df[c])
        ]

    def create_plan(self) -> List[Dict[str, Any]]:
        plan: List[VisualizationPlanItem] = []

        # 1. Dataset Overview Visuals
        has_missing = any(r.get("missing_count", 0) > 0 for r in self.missing_reports) or (self.df.isna().sum().sum() > 0)
        if has_missing:
            plan.append(
                VisualizationPlanItem(
                    plot_type="missing_matrix",
                    feature="all_columns",
                    reason="Multiple columns contain null values; visualizes missingness patterns and co-occurrence.",
                    priority="high",
                    category="overview",
                )
            )

        # 2. Target Column Visualizations
        if self.target_col and self.target_col in self.df.columns:
            if self.task_type == "classification" or self.df[self.target_col].nunique() <= 10:
                plan.append(
                    VisualizationPlanItem(
                        plot_type="class_distribution",
                        feature=self.target_col,
                        reason="Assesses class balance and minority representation for appropriate loss weighting and metric selection.",
                        priority="high",
                        category="target",
                    )
                )
            else:
                plan.append(
                    VisualizationPlanItem(
                        plot_type="target_histogram_kde",
                        feature=self.target_col,
                        reason="Assesses continuous target normality, kurtosis, and target transformation necessity.",
                        priority="high",
                        category="target",
                    )
                )

        # 3. High-Priority Numerical Features (Skewness, Outliers, or Bimodal)
        for col in self.num_cols:
            if col == self.target_col:
                continue
            s = self.df[col].dropna()
            if len(s) < 5:
                continue

            skew = float(s.skew()) if not pd.isna(s.skew()) else 0.0
            col_outliers = [r for r in self.outlier_reports if r.get("column") == col and r.get("outlier_count", 0) > 0]

            if abs(skew) > 1.5 or len(col_outliers) > 0:
                plan.append(
                    VisualizationPlanItem(
                        plot_type="boxplot",
                        feature=col,
                        reason=f"Significant skewness ({round(skew, 2)}) and {len(col_outliers)} outlier indicator(s).",
                        priority="high",
                        category="numerical",
                    )
                )
            elif len(plan) < 8:
                plan.append(
                    VisualizationPlanItem(
                        plot_type="histogram_kde",
                        feature=col,
                        reason="Symmetric continuous feature; verifies Gaussian bell-curve and variance properties.",
                        priority="medium",
                        category="numerical",
                    )
                )

        # 4. Key Categorical Features
        for col in self.cat_cols:
            if col == self.target_col:
                continue
            n_unique = self.df[col].nunique()
            if 2 <= n_unique <= 20:
                if self.target_col and (self.task_type == "classification" or self.df[self.target_col].nunique() <= 10):
                    plan.append(
                        VisualizationPlanItem(
                            plot_type="target_distribution_by_category",
                            feature=col,
                            target_feature=self.target_col,
                            reason=f"Categorical '{col}' has {n_unique} distinct levels; inspects target rate conditional on category.",
                            priority="high",
                            category="categorical",
                        )
                    )
                else:
                    plan.append(
                        VisualizationPlanItem(
                            plot_type="countplot",
                            feature=col,
                            reason=f"Moderate cardinality ({n_unique} classes); reveals frequency distribution and class imbalance.",
                            priority="medium",
                            category="categorical",
                        )
                    )

        # 5. Correlation & Bivariate Relationships
        if len(self.num_cols) >= 3:
            plan.append(
                VisualizationPlanItem(
                    plot_type="correlation_heatmap",
                    feature="numerical_matrix",
                    reason="Multivariate correlation scan identifies collinear predictor clusters and candidate target correlations.",
                    priority="high",
                    category="relationships",
                )
            )

        # 6. Target vs Top Numerical Predictor (Scatter or Grouped Violin)
        if self.target_col and len(self.num_cols) > 0:
            top_num = [c for c in self.num_cols if c != self.target_col]
            if top_num:
                if self.task_type == "classification" or self.df[self.target_col].nunique() <= 10:
                    plan.append(
                        VisualizationPlanItem(
                            plot_type="violin_by_target",
                            feature=top_num[0],
                            target_feature=self.target_col,
                            reason=f"Compares distribution of primary feature '{top_num[0]}' across target classes.",
                            priority="high",
                            category="relationships",
                        )
                    )
                else:
                    plan.append(
                        VisualizationPlanItem(
                            plot_type="scatter_with_trend",
                            feature=top_num[0],
                            target_feature=self.target_col,
                            reason=f"Bivariate scatter with OLS trend line between '{top_num[0]}' and continuous target.",
                            priority="high",
                            category="relationships",
                        )
                    )

        # Sort: high priority first, max 10 planned charts to keep UI responsive
        sorted_plan = sorted(plan, key=lambda x: 0 if x.priority == "high" else (1 if x.priority == "medium" else 2))
        return [item.to_dict() for item in sorted_plan[:10]]


def plan_visualizations(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    task_type: Optional[str] = None,
    outlier_reports: Optional[List[Dict[str, Any]]] = None,
    distribution_reports: Optional[Dict[str, Any]] = None,
    missing_reports: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    planner = VisualizationPlanner(
        df=df,
        target_col=target_col,
        task_type=task_type,
        outlier_reports=outlier_reports,
        distribution_reports=distribution_reports,
        missing_reports=missing_reports,
    )
    return planner.create_plan()


def recommend_plots_for_column(df: pd.DataFrame, column: str) -> List[str]:
    if column not in df.columns:
        return []
    if pd.api.types.is_numeric_dtype(df[column]):
        return ["histogram", "kde", "boxplot", "violin"]
    else:
        return ["bar_chart", "pie_chart", "count_plot"]

