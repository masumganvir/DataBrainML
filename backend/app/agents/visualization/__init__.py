"""
DataWise AI — Visualization Agents
Agents for exploratory analysis, chart selection, and deterministic visual rendering.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.visualization_tools import (
    generate_visualization,
    generate_eda_figures,
    plan_visualizations,
    analyze_distributions,
    calculate_correlations,
)


class EDAAgent(BaseAgent):
    """
    Executes automated exploratory data analysis: correlations, distributions, skewness, class balance.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="EDAAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            dist_res = analyze_distributions(df)
            corr_res = calculate_correlations(df)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "distributions": dist_res,
                    "correlations": corr_res,
                    "summary_statistics": df.describe(include="all").to_dict(),
                },
                summary=f"EDA completed: analyzed distributions for {len(dist_res.get('numerical_features', []))} numerical features and calculated correlation matrix."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"EDA failed: {e}"
            )


class PlotSelectionAgent(BaseAgent):
    """
    Selects the most insightful, high-value visualizations based on data modality and analytical intent.
    Prevents overwhelming the user with redundant plots.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="PlotSelectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            plan = plan_visualizations(df, target_col=target_col)
            plots = plan if isinstance(plan, list) else plan.get("recommended_plots", [])

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"recommended_plots": plots},
                summary=f"Curated {len(plots)} targeted visualizations focusing on target distribution, feature correlations, and outlier spreads."
            )

        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Plot selection planning failed: {e}"
            )


class VisualizationAgent(BaseAgent):
    """
    Executes rendering of interactive and publication-quality plots.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="VisualizationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        plot_type = input_data.parameters.get("plot_type", "correlation_heatmap")
        columns = input_data.parameters.get("columns", [])

        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            vis_result = generate_visualization(df, plot_type=plot_type, columns=columns)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=vis_result,
                summary=f"Rendered '{plot_type}' successfully."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Visualization rendering failed: {e}"
            )


__all__ = [
    "EDAAgent",
    "PlotSelectionAgent",
    "VisualizationAgent",
]
