"""
DataWise AI — Interactive Visualization Engine

Creates rich, modern dark-themed Plotly visualizations:
  - Smart automatic plot selection based on variable types and cardinality:
      * Numerical distribution: Histogram with density estimation & box plot
      * Categorical distribution: Sorted bar chart with top categories
      * Correlation heatmap: Interactive matrix with diverging colorscale
      * Missing value overview: Missingness percentage bar chart
      * Numerical vs Numerical: Scatter plot with trend line
      * Numerical vs Categorical: Box & violin distribution comparison
  - Exports:
      * Plotly JSON specs (consumed by frontend React-Plotly)
      * Standalone responsive HTML artifacts
  - Concise AI interpretation for every generated visual
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger

from app.config.settings import get_settings

settings = get_settings()

DARK_LAYOUT = dict(
    paper_bgcolor="#090d16",
    plot_bgcolor="#0f172a",
    font=dict(family="'Plus Jakarta Sans', sans-serif", color="#f8fafc", size=12),
    xaxis=dict(
        gridcolor="rgba(148, 163, 184, 0.12)",
        zerolinecolor="rgba(148, 163, 184, 0.2)",
        tickfont=dict(color="#94a3b8"),
    ),
    yaxis=dict(
        gridcolor="rgba(148, 163, 184, 0.12)",
        zerolinecolor="rgba(148, 163, 184, 0.2)",
        tickfont=dict(color="#94a3b8"),
    ),
    margin=dict(l=40, r=40, t=50, b=40),
)


class VisualizationEngine:
    """Generates modern interactive plots with AI interpretations."""

    def __init__(self, df: pd.DataFrame, session_id: str):
        self.df = df
        self.session_id = session_id
        self.plots_dir = settings.artifacts_dir_path / "plots" / session_id
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    def _save_html_artifact(self, fig: go.Figure, chart_name: str) -> str:
        """Saves a standalone HTML plot artifact to disk."""
        clean_name = f"{chart_name}.html".replace(" ", "_").lower()
        file_path = self.plots_dir / clean_name
        fig.write_html(str(file_path), include_plotlyjs="cdn", full_html=True)
        return str(file_path.resolve())

    def plot_numerical_distribution(self, col: str) -> Dict[str, Any]:
        """Histogram + marginal box plot for a numerical column."""
        s = self.df[col].dropna()
        skew_val = float(s.skew()) if len(s) > 2 else 0.0

        fig = px.histogram(
            self.df,
            x=col,
            marginal="box",
            nbins=35,
            color_discrete_sequence=["#6366f1"],
            title=f"Distribution of {col}",
        )
        fig.update_layout(**DARK_LAYOUT)
        fig.update_traces(marker_line_color="#818cf8", marker_line_width=1, opacity=0.85)

        html_path = self._save_html_artifact(fig, f"hist_{col}")

        # AI interpretation
        skew_desc = "approximately symmetric" if abs(skew_val) <= 0.5 else ("right-skewed (positive tail)" if skew_val > 0 else "left-skewed (negative tail)")
        interpretation = (
            f"Column '{col}' exhibits a {skew_desc} distribution (skewness = {skew_val:.2f}) "
            f"with median {float(s.median()):.2f} and standard deviation {float(s.std()):.2f}."
        )

        return {
            "chart_type": "histogram",
            "column": col,
            "title": f"Distribution of {col}",
            "html_path": html_path,
            "figure_json": json.loads(fig.to_json()),
            "interpretation": interpretation,
        }

    def plot_categorical_distribution(self, col: str, top_n: int = 15) -> Dict[str, Any]:
        """Bar chart for top categorical counts."""
        s = self.df[col].dropna()
        counts = s.value_counts()
        total_unique = len(counts)

        if total_unique > top_n:
            top_counts = counts.head(top_n)
            other_sum = counts.iloc[top_n:].sum()
            plot_df = pd.concat([top_counts, pd.Series({"Other": other_sum})]).reset_index()
        else:
            plot_df = counts.reset_index()

        plot_df.columns = ["category", "count"]

        fig = px.bar(
            plot_df,
            x="category",
            y="count",
            color_discrete_sequence=["#a855f7"],
            title=f"Frequency Breakdown: {col}",
        )
        fig.update_layout(**DARK_LAYOUT)
        fig.update_traces(marker_line_color="#c084fc", marker_line_width=1, opacity=0.9)

        html_path = self._save_html_artifact(fig, f"bar_{col}")

        top_cat = counts.index[0]
        top_pct = round(counts.iloc[0] / len(s) * 100, 1)
        interpretation = (
            f"Categorical feature '{col}' has {total_unique} distinct categories. "
            f"The dominant category is '{top_cat}', comprising {top_pct}% of non-null records."
        )

        return {
            "chart_type": "bar",
            "column": col,
            "title": f"Frequency Breakdown: {col}",
            "html_path": html_path,
            "figure_json": json.loads(fig.to_json()),
            "interpretation": interpretation,
        }

    def plot_correlation_heatmap(self) -> Optional[Dict[str, Any]]:
        """Interactive correlation heatmap for numerical features."""
        num_df = self.df.select_dtypes(include=[np.number])
        if num_df.shape[1] < 2:
            return None

        corr = num_df.corr().round(2)
        cols = list(corr.columns)

        fig = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=cols,
                y=cols,
                colorscale=[[0.0, "#06b6d4"], [0.5, "#0f172a"], [1.0, "#ec4899"]],
                zmin=-1.0,
                zmax=1.0,
                text=corr.values,
                texttemplate="%{text}",
                textfont=dict(color="#f8fafc", size=10),
                colorbar=dict(tickfont=dict(color="#94a3b8")),
            )
        )
        fig.update_layout(title="Feature Correlation Matrix (Pearson)", **DARK_LAYOUT)

        html_path = self._save_html_artifact(fig, "correlation_heatmap")

        # Find highest positive correlation pair (excluding self-correlation)
        unstacked = corr.unstack()
        non_diag = unstacked[unstacked.index.get_level_values(0) != unstacked.index.get_level_values(1)]
        if not non_diag.empty:
            strongest_pos = non_diag.idxmax()
            pos_val = float(non_diag.max())
            interpretation = (
                f"Analyzed {len(cols)} numerical features. Highest positive correlation: "
                f"'{strongest_pos[0]}' & '{strongest_pos[1]}' (r = {pos_val:.2f})."
            )
        else:
            interpretation = f"Analyzed {len(cols)} numerical features correlation matrix."

        return {
            "chart_type": "heatmap",
            "column": None,
            "title": "Feature Correlation Matrix (Pearson)",
            "html_path": html_path,
            "figure_json": json.loads(fig.to_json()),
            "interpretation": interpretation,
        }

    def plot_missing_values_matrix(self) -> Optional[Dict[str, Any]]:
        """Missing values bar chart showing percentage per column."""
        missing = (self.df.isnull().sum() / len(self.df) * 100).round(2)
        missing = missing[missing > 0].sort_values(ascending=False)

        if missing.empty:
            return None

        plot_df = missing.reset_index()
        plot_df.columns = ["column", "missing_pct"]

        fig = px.bar(
            plot_df,
            x="column",
            y="missing_pct",
            color="missing_pct",
            color_continuous_scale="Reds",
            title="Missing Values Summary (% per Column)",
        )
        fig.update_layout(**DARK_LAYOUT)

        html_path = self._save_html_artifact(fig, "missing_values_summary")

        worst_col = plot_df.iloc[0]["column"]
        worst_pct = plot_df.iloc[0]["missing_pct"]
        interpretation = (
            f"Identified {len(plot_df)} columns with missing data. "
            f"'{worst_col}' has the highest missingness ({worst_pct}%)."
        )

        return {
            "chart_type": "bar",
            "column": None,
            "title": "Missing Values Summary (% per Column)",
            "html_path": html_path,
            "figure_json": json.loads(fig.to_json()),
            "interpretation": interpretation,
        }

    def plot_bivariate(self, x_col: str, y_col: str) -> Dict[str, Any]:
        """Scatter plot with trendline for 2 numerical columns."""
        clean_df = self.df[[x_col, y_col]].dropna()
        fig = px.scatter(
            clean_df,
            x=x_col,
            y=y_col,
            opacity=0.7,
            color_discrete_sequence=["#06b6d4"],
            title=f"Relationship: {x_col} vs {y_col}",
        )

        if len(clean_df) > 1 and clean_df[x_col].nunique() > 1:
            try:
                slope, intercept = np.polyfit(clean_df[x_col], clean_df[y_col], 1)
                x_vals = np.linspace(clean_df[x_col].min(), clean_df[x_col].max(), 50)
                y_vals = slope * x_vals + intercept
                fig.add_trace(
                    go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines",
                        name="Trendline",
                        line=dict(color="#ec4899", width=2, dash="dash"),
                    )
                )
            except Exception:
                pass

        fig.update_layout(**DARK_LAYOUT)
        html_path = self._save_html_artifact(fig, f"scatter_{x_col}_{y_col}")

        corr = float(clean_df[x_col].corr(clean_df[y_col]))
        trend_desc = "positive" if corr > 0.3 else ("negative" if corr < -0.3 else "weak / non-linear")
        interpretation = (
            f"Scatter analysis between '{x_col}' and '{y_col}' reveals a {trend_desc} correlation (r = {corr:.2f})."
        )

        return {
            "chart_type": "scatter",
            "column": f"{x_col}_vs_{y_col}",
            "title": f"Relationship: {x_col} vs {y_col}",
            "html_path": html_path,
            "figure_json": json.loads(fig.to_json()),
            "interpretation": interpretation,
        }

    def generate_recommended_suite(self, max_plots: int = 6) -> List[Dict[str, Any]]:
        """Autonomously constructs an optimal suite of exploratory visualizations."""
        plots: List[Dict[str, Any]] = []

        # 1. Missing values overview (if any)
        missing_plot = self.plot_missing_values_matrix()
        if missing_plot:
            plots.append(missing_plot)

        # 2. Correlation heatmap
        corr_plot = self.plot_correlation_heatmap()
        if corr_plot:
            plots.append(corr_plot)

        # 3. Key numerical distributions
        num_cols = [
            c for c in self.df.columns
            if pd.api.types.is_numeric_dtype(self.df[c]) and not pd.api.types.is_bool_dtype(self.df[c])
            and self.df[c].nunique() > 2
        ]
        for col in num_cols[:2]:
            if len(plots) >= max_plots:
                break
            plots.append(self.plot_numerical_distribution(str(col)))

        # 4. Key categorical distributions
        cat_cols = [
            c for c in self.df.columns
            if (self.df[c].dtype == object or pd.api.types.is_string_dtype(self.df[c]))
            and 1 < self.df[c].nunique() <= 30
        ]
        for col in cat_cols[:2]:
            if len(plots) >= max_plots:
                break
            plots.append(self.plot_categorical_distribution(str(col)))

        # 5. Top bivariate relationship (if >= 2 numerical cols)
        if len(num_cols) >= 2 and len(plots) < max_plots:
            plots.append(self.plot_bivariate(str(num_cols[0]), str(num_cols[1])))

        return plots
