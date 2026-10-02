"""
DataWise AI — Agent 03: EDA & Visualization Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.visualization import (
    generate_distribution_spec,
    generate_categorical_spec,
    generate_correlation_matrix_spec,
    generate_outlier_plot_spec,
    generate_scatter_spec,
)


class VisualizationAgent:
    """Agent 03: Selects and formats high-impact visual exploratory plots."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "EDA & Visualization Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                path = input_data.dataset_path
                ext = Path(path).suffix.lower()
                if ext in (".xlsx", ".xls"):
                    df = pd.read_excel(path)
                elif ext == ".json":
                    df = pd.read_json(path)
                else:
                    df = pd.read_csv(path, low_memory=False)

                plots: List[Dict[str, Any]] = []
                target = input_data.parameters.get("target_column")

                # 1. Target plot if specified
                if target and target in df.columns:
                    if pd.api.types.is_numeric_dtype(df[target]):
                        plots.append({
                            "spec": generate_distribution_spec(df[target]),
                            "reason": f"Understand target '{target}' spread, skewness, and tails.",
                            "interpretation": f"Baseline distribution of target variable '{target}'.",
                            "priority": "HIGH",
                        })
                    else:
                        plots.append({
                            "spec": generate_categorical_spec(df[target]),
                            "reason": f"Inspect class balance for target '{target}'.",
                            "interpretation": f"Class distribution for classification target '{target}'.",
                            "priority": "HIGH",
                        })

                # 2. Correlation heatmap
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) >= 2:
                    plots.append({
                        "spec": generate_correlation_matrix_spec(df),
                        "reason": "Identify multi-collinearity and linear predictive signals.",
                        "interpretation": "Pairwise Pearson correlation coefficients across numerical features.",
                        "priority": "HIGH",
                    })

                # 3. Top numerical distribution
                for col in numeric_cols:
                    if col != target:
                        plots.append({
                            "spec": generate_distribution_spec(df[col]),
                            "reason": f"Inspect density and shape for feature '{col}'.",
                            "interpretation": f"Distribution spread for '{col}'.",
                            "priority": "MEDIUM",
                        })
                        plots.append({
                            "spec": generate_outlier_plot_spec(df[col]),
                            "reason": f"Detect outlier extremes for feature '{col}'.",
                            "interpretation": f"IQR box plot boundary diagnostics for '{col}'.",
                            "priority": "MEDIUM",
                        })
                        break

                # 4. Top categorical bar plot
                cat_cols = df.select_dtypes(exclude=[np.number]).columns
                for col in cat_cols:
                    if col != target:
                        plots.append({
                            "spec": generate_categorical_spec(df[col]),
                            "reason": f"Assess category dominance and sparsity for '{col}'.",
                            "interpretation": f"Top category frequency counts for '{col}'.",
                            "priority": "LOW",
                        })
                        break

                summary = f"EDA Agent generated {len(plots)} prioritized visual specifications."
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={"visualizations": plots, "total_plots": len(plots)},
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "visualization_engine", "status": "ready"},
                summary="EDA & Visualization Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Visualization Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"EDA Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
