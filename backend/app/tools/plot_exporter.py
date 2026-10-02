"""
DataWise AI — Real Visualizations & Plot Exporter
Generates genuine Matplotlib/Seaborn .png visualization artifacts:
- Numerical distributions (Histograms, KDE, Box plots)
- Categorical frequencies (Bar charts)
- Correlation Heatmap
- Feature vs Target relationships
- Evaluation plots (Confusion Matrix / Residuals, ROC / PR curves, Feature Importance)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger


def export_pipeline_visualizations(
    df: pd.DataFrame,
    target_col: str,
    task_type: str,
    output_dir: Path,
    champion_pipeline: Optional[Any] = None,
    X_test: Optional[pd.DataFrame] = None,
    y_test: Optional[pd.Series] = None,
) -> Dict[str, List[str]]:
    """
    Generates and saves genuine PNG plots to the structured artifact directories.
    Returns a dictionary of generated file paths by category.
    """
    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update({"figure.autolayout": True, "font.sans-serif": "DejaVu Sans"})

    # Setup directories
    dist_dir = output_dir / "distributions"
    miss_dir = output_dir / "missing_values"
    outl_dir = output_dir / "outliers"
    corr_dir = output_dir / "correlations"
    feat_dir = output_dir / "features"
    eval_dir = output_dir / "evaluation"

    for d in [dist_dir, miss_dir, outl_dir, corr_dir, feat_dir, eval_dir]:
        d.mkdir(parents=True, exist_ok=True)

    generated: Dict[str, List[str]] = {
        "distributions": [],
        "missing_values": [],
        "outliers": [],
        "correlations": [],
        "features": [],
        "evaluation": [],
    }

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
    categorical_cols = [c for c in df.select_dtypes(exclude=[np.number]).columns if c != target_col]

    # 1. Numerical Distributions (Histograms + KDE)
    for col in numeric_cols[:4]:
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            clean_series = df[col].dropna()
            if not clean_series.empty:
                sns.histplot(clean_series, kde=True, ax=ax, color="#4f46e5")
                ax.set_title(f"Distribution: {col}", fontsize=12, fontweight="bold")
                ax.set_xlabel(col)
                ax.set_ylabel("Frequency")
                save_path = dist_dir / f"{col}_distribution.png"
                fig.savefig(save_path, dpi=120, bbox_inches="tight")
                generated["distributions"].append(str(save_path))
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Error plotting distribution for {col}: {e}")
            plt.close("all")

    # 2. Outlier Analysis (Boxplots)
    for col in numeric_cols[:3]:
        try:
            fig, ax = plt.subplots(figsize=(6, 3))
            clean_series = df[col].dropna()
            if not clean_series.empty:
                sns.boxplot(x=clean_series, ax=ax, color="#ec4899", fliersize=4)
                ax.set_title(f"Outlier Analysis: {col}", fontsize=12, fontweight="bold")
                ax.set_xlabel(col)
                save_path = outl_dir / f"{col}_boxplot.png"
                fig.savefig(save_path, dpi=120, bbox_inches="tight")
                generated["outliers"].append(str(save_path))
            plt.close(fig)
        except Exception as e:
            logger.warning(f"Error plotting boxplot for {col}: {e}")
            plt.close("all")

    # 3. Missing Value Analysis
    try:
        missing_counts = df.isnull().sum()
        fig, ax = plt.subplots(figsize=(8, 4))
        if missing_counts.sum() > 0:
            missing_filtered = missing_counts[missing_counts > 0]
            missing_filtered.plot(kind="bar", ax=ax, color="#f59e0b")
            ax.set_title("Missing Value Counts by Feature", fontsize=12, fontweight="bold")
            ax.set_ylabel("Missing Count")
        else:
            ax.text(0.5, 0.5, "Zero Missing Values Detected\n(Dataset is Complete)", 
                    ha="center", va="center", fontsize=13, color="#10b981", fontweight="bold")
            ax.set_title("Missing Value Status", fontsize=12, fontweight="bold")
            ax.axis("off")
        save_path = miss_dir / "missing_values_summary.png"
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        generated["missing_values"].append(str(save_path))
        plt.close(fig)
    except Exception as e:
        logger.warning(f"Error plotting missing values: {e}")
        plt.close("all")

    # 4. Correlation Heatmap
    try:
        all_numeric = df.select_dtypes(include=[np.number])
        if all_numeric.shape[1] > 1:
            corr = all_numeric.corr()
            fig, ax = plt.subplots(figsize=(max(6, min(12, corr.shape[1])), max(5, min(10, corr.shape[1]))))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, square=True)
            ax.set_title("Pearson Correlation Heatmap", fontsize=13, fontweight="bold")
            save_path = corr_dir / "correlation_heatmap.png"
            fig.savefig(save_path, dpi=120, bbox_inches="tight")
            generated["correlations"].append(str(save_path))
            plt.close(fig)
    except Exception as e:
        logger.warning(f"Error plotting correlation heatmap: {e}")
        plt.close("all")

    # 5. Feature vs Target Relationship
    if target_col in df.columns:
        try:
            is_reg = "regression" in task_type.lower()
            if numeric_cols:
                top_feature = numeric_cols[0]
                fig, ax = plt.subplots(figsize=(6, 4))
                if is_reg and pd.api.types.is_numeric_dtype(df[target_col]):
                    sns.regplot(data=df, x=top_feature, y=target_col, ax=ax, scatter_kws={"alpha": 0.5}, line_kws={"color": "red"})
                    ax.set_title(f"Target vs Feature: {top_feature}", fontsize=12, fontweight="bold")
                else:
                    sns.boxplot(data=df, x=target_col, y=top_feature, ax=ax, palette="Set2")
                    ax.set_title(f"{top_feature} by Target Class ({target_col})", fontsize=12, fontweight="bold")
                save_path = feat_dir / "feature_target_relationship.png"
                fig.savefig(save_path, dpi=120, bbox_inches="tight")
                generated["features"].append(str(save_path))
                plt.close(fig)
        except Exception as e:
            logger.warning(f"Error plotting feature-target relationship: {e}")
            plt.close("all")

    # 6. Evaluation Plots
    if champion_pipeline is not None and X_test is not None and y_test is not None:
        try:
            is_reg = "regression" in task_type.lower()
            y_pred = champion_pipeline.predict(X_test)

            if not is_reg:
                # Confusion Matrix
                from sklearn.metrics import confusion_matrix
                cm = confusion_matrix(y_test, y_pred)
                fig, ax = plt.subplots(figsize=(5, 4))
                sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
                ax.set_title("Holdout Test Confusion Matrix", fontsize=12, fontweight="bold")
                ax.set_xlabel("Predicted Label")
                ax.set_ylabel("True Label")
                cm_path = eval_dir / "confusion_matrix.png"
                fig.savefig(cm_path, dpi=120, bbox_inches="tight")
                generated["evaluation"].append(str(cm_path))
                plt.close(fig)

                # ROC Curve if probabilities exist
                if hasattr(champion_pipeline, "predict_proba"):
                    try:
                        from sklearn.metrics import roc_curve, auc
                        proba = champion_pipeline.predict_proba(X_test)
                        if proba.shape[1] == 2:
                            fpr, tpr, _ = roc_curve(y_test, proba[:, 1])
                            roc_auc = auc(fpr, tpr)
                            fig, ax = plt.subplots(figsize=(5, 4))
                            ax.plot(fpr, tpr, color="#4f46e5", lw=2, label=f"ROC (AUC = {roc_auc:.3f})")
                            ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--")
                            ax.set_xlabel("False Positive Rate")
                            ax.set_ylabel("True Positive Rate")
                            ax.set_title("ROC Curve", fontsize=12, fontweight="bold")
                            ax.legend(loc="lower right")
                            roc_path = eval_dir / "roc_curve.png"
                            fig.savefig(roc_path, dpi=120, bbox_inches="tight")
                            generated["evaluation"].append(str(roc_path))
                            plt.close(fig)
                    except Exception:
                        plt.close("all")
            else:
                # Residuals & Actual vs Predicted
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
                ax1.scatter(y_test, y_pred, alpha=0.6, color="#4f46e5")
                min_val = min(y_test.min(), y_pred.min())
                max_val = max(y_test.max(), y_pred.max())
                ax1.plot([min_val, max_val], [min_val, max_val], color="red", linestyle="--")
                ax1.set_xlabel("Actual Values")
                ax1.set_ylabel("Predicted Values")
                ax1.set_title("Actual vs Predicted", fontsize=11, fontweight="bold")

                residuals = y_test - y_pred
                sns.histplot(residuals, kde=True, ax=ax2, color="#06b6d4")
                ax2.set_xlabel("Residual (Actual - Predicted)")
                ax2.set_title("Residuals Distribution", fontsize=11, fontweight="bold")
                save_path = eval_dir / "residuals_plot.png"
                fig.savefig(save_path, dpi=120, bbox_inches="tight")
                generated["evaluation"].append(str(save_path))
                plt.close(fig)

            # Feature Importance
            model_step = getattr(champion_pipeline, "named_steps", {}).get("model", champion_pipeline)
            importances = None
            if hasattr(model_step, "feature_importances_"):
                importances = model_step.feature_importances_
            elif hasattr(model_step, "coef_"):
                coef = model_step.coef_
                importances = np.abs(coef[0] if coef.ndim > 1 else coef)

            if importances is not None and len(importances) > 0:
                fig, ax = plt.subplots(figsize=(7, max(4, min(8, len(importances) * 0.3))))
                feat_names = [f"F_{i}" for i in range(len(importances))]
                # If preprocessor step has get_feature_names_out:
                prep = getattr(champion_pipeline, "named_steps", {}).get("preprocessor")
                if prep and hasattr(prep, "get_feature_names_out"):
                    try:
                        feat_names = list(prep.get_feature_names_out())
                    except Exception:
                        pass
                
                # Show top 12
                top_indices = np.argsort(importances)[-12:]
                y_ticks = np.arange(len(top_indices))
                ax.barh(y_ticks, importances[top_indices], color="#3b82f6")
                ax.set_yticks(y_ticks)
                ax.set_yticklabels([feat_names[i] if i < len(feat_names) else f"Feature {i}" for i in top_indices], fontsize=9)
                ax.set_xlabel("Importance")
                ax.set_title("Feature Importances", fontsize=12, fontweight="bold")
                save_path = eval_dir / "feature_importance.png"
                fig.savefig(save_path, dpi=120, bbox_inches="tight")
                generated["evaluation"].append(str(save_path))
                plt.close(fig)

        except Exception as e:
            logger.warning(f"Error plotting evaluation charts: {e}")
            plt.close("all")

    return generated
