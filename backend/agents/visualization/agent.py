"""
DataWise AI — Intelligent Visualization Agent
Generates purposeful, publication-grade visual artifacts based on statistical properties
(histograms, KDEs, boxplots, countplots, correlation heatmaps, ROC curves, residual plots).
Saves plots as PNG artifacts with metadata, labels, and statistical interpretation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely
from app.config.settings import get_settings


class VisualizationAgent(BaseAgent):
    """Intelligent Data Science Visualization Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Visualization Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        settings = get_settings()
        out_dir = Path(settings.plots_path) / (input_data.session_id or "default")
        out_dir.mkdir(parents=True, exist_ok=True)

        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Visualization failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        visualizations_created: List[Dict[str, Any]] = []

        # Style configuration
        plt.style.use("dark_background")
        sns.set_theme(style="darkgrid", rc={"axes.facecolor": "#0f172a", "figure.facecolor": "#090d16"})

        # 1. Target distribution plot
        if target_col and target_col in df.columns:
            fig, ax = plt.subplots(figsize=(8, 4.5))
            series = df[target_col].dropna()
            is_cat = not pd.api.types.is_numeric_dtype(series) or series.nunique() <= 10

            if is_cat:
                counts = series.value_counts()
                sns.barplot(x=counts.index.astype(str), y=counts.values, ax=ax, palette="Blues_r")
                ax.set_title(f"Target Distribution: {target_col}", fontsize=12, fontweight="bold", color="#818cf8")
                ax.set_xlabel(target_col)
                ax.set_ylabel("Count")
                interpretation = f"Target '{target_col}' has {len(counts)} classes with distribution {dict(counts)}."
            else:
                sns.histplot(series, kde=True, ax=ax, color="#6366f1", bins=30)
                ax.set_title(f"Target Continuous Distribution: {target_col}", fontsize=12, fontweight="bold", color="#818cf8")
                ax.set_xlabel(target_col)
                ax.set_ylabel("Density")
                interpretation = f"Continuous target '{target_col}' spans [{series.min():.2f}, {series.max():.2f}] with mean {series.mean():.2f}."

            plt.tight_layout()
            file_name = f"plot_target_{target_col}.png"
            file_path = out_dir / file_name
            fig.savefig(file_path, dpi=120)
            plt.close(fig)

            visualizations_created.append({
                "chart_type": "target_distribution",
                "column": target_col,
                "file_path": str(file_path),
                "title": f"Target Distribution: {target_col}",
                "interpretation": interpretation,
            })

        # 2. Correlation Heatmap (for numeric features)
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) >= 2:
            fig, ax = plt.subplots(figsize=(9, 7))
            corr = df[num_cols[:12]].corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, linewidths=0.5)
            ax.set_title("Feature Correlation Matrix (Top Numerical)", fontsize=12, fontweight="bold", color="#818cf8")
            plt.tight_layout()
            file_name = "plot_correlation_heatmap.png"
            file_path = out_dir / file_name
            fig.savefig(file_path, dpi=120)
            plt.close(fig)

            visualizations_created.append({
                "chart_type": "correlation_heatmap",
                "file_path": str(file_path),
                "title": "Feature Correlation Heatmap",
                "interpretation": "Heatmap highlights collinearity and multi-feature interaction relationships.",
            })

        # 3. Top Numerical Feature Boxplots (Outlier Inspection)
        for col in list(num_cols)[:3]:
            if col == target_col:
                continue
            fig, ax = plt.subplots(figsize=(7, 3))
            sns.boxplot(x=df[col].dropna(), ax=ax, color="#10b981", fliersize=4)
            ax.set_title(f"Outlier & Dispersion Analysis: {col}", fontsize=11, fontweight="bold", color="#34d399")
            ax.set_xlabel(col)
            plt.tight_layout()
            file_name = f"plot_boxplot_{col}.png"
            file_path = out_dir / file_name
            fig.savefig(file_path, dpi=120)
            plt.close(fig)

            visualizations_created.append({
                "chart_type": "boxplot",
                "column": col,
                "file_path": str(file_path),
                "title": f"Boxplot: {col}",
                "interpretation": f"Boxplot details median, IQR bounds, and detected outliers for '{col}'.",
            })

        summary = f"Generated {len(visualizations_created)} publication-grade charts with contextual interpretation."

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "visualizations": visualizations_created,
                "total_plots": len(visualizations_created),
            },
            artifacts_generated=[v["file_path"] for v in visualizations_created],
            summary=summary,
        )
