"""
DataWise AI — EDA LangGraph Orchestrator
Sections 4 & 5 Specification:
Constructs and executes the complete End-to-End EDA + Visualization + Dimensionality Reduction Engine:
START
  ↓
Dataset Profiler
  ↓
Data Quality
  ↓
Target Analysis
  ↓
Outlier Analysis (Never deletes blindly)
  ↓
Univariate EDA
  ↓
Bivariate EDA
  ↓
Multivariate EDA (Safely sampled)
  ↓
Distribution Analysis
  ↓
Correlation Analysis & Multicollinearity (VIF)
  ↓
Categorical & Numerical Analysis
  ↓
Temporal Analysis (if datetime columns exist)
  ↓
Feature Relationship Analysis
  ↓
Dimensionality Reduction & PCA (Evaluates original vs PCA)
  ↓
Feature Extraction & Selection (Zero leakage)
  ↓
Visualization Planner (Never creates images directly)
  ↓
Visualization Executor (Renders PNGs & HTML)
  ↓
Visualization Validator (Graph loop retry)
  ↓
Insight Generator
  ↓
EDA Report Agent (EDA_Report.html + eda_summary.json)
  ↓
END
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
import pandas as pd

from backend.agents.eda.eda_state import EDAState, create_initial_eda_state
from backend.agents.eda.dataset_profiler_agent import DatasetProfilerAgent
from backend.agents.eda.data_quality_agent import DataQualityAgent
from backend.agents.eda.outlier_analysis_agent import OutlierAnalysisAgent
from backend.agents.eda.univariate_eda_agent import UnivariateEDAAgent
from backend.agents.eda.bivariate_eda_agent import BivariateEDAAgent
from backend.agents.eda.multivariate_eda_agent import MultivariateEDAAgent
from backend.agents.eda.distribution_analysis_agent import DistributionAnalysisAgent
from backend.agents.eda.correlation_analysis_agent import CorrelationAnalysisAgent
from backend.agents.eda.categorical_analysis_agent import CategoricalAnalysisAgent
from backend.agents.eda.numerical_analysis_agent import NumericalAnalysisAgent
from backend.agents.eda.temporal_analysis_agent import TemporalAnalysisAgent
from backend.agents.eda.target_analysis_agent import TargetAnalysisAgent
from backend.agents.eda.feature_relationship_agent import FeatureRelationshipAgent
from backend.agents.eda.pca_agent import PCAAgent
from backend.agents.eda.dimensionality_reduction_agent import DimensionalityReductionAgent
from backend.agents.eda.feature_extraction_agent import FeatureExtractionAgent
from backend.agents.eda.feature_selection_agent import FeatureSelectionAgent
from backend.agents.eda.visualization_planner_agent import VisualizationPlannerAgent
from backend.agents.eda.visualization_executor_agent import VisualizationExecutorAgent
from backend.agents.eda.visualization_validator_agent import VisualizationValidatorAgent
from backend.agents.eda.insight_generation_agent import InsightGenerationAgent
from backend.agents.eda.eda_report_agent import EDAReportAgent
from backend.agents.eda.eda_fallback_agent import EDAFallbackAgent


class EDAOrchestrator:
    """Master orchestrator for the EDA, Visualization, and Dimensionality Reduction Subsystem."""

    def __init__(self, output_dir: Optional[str] = None):
        self._default_output_dir = output_dir
        self.profiler = DatasetProfilerAgent()
        self.quality = DataQualityAgent()
        self.target = TargetAnalysisAgent()
        self.outlier = OutlierAnalysisAgent()
        self.univariate = UnivariateEDAAgent()
        self.bivariate = BivariateEDAAgent()
        self.multivariate = MultivariateEDAAgent()
        self.distribution = DistributionAnalysisAgent()
        self.correlation = CorrelationAnalysisAgent()
        self.categorical = CategoricalAnalysisAgent()
        self.numerical = NumericalAnalysisAgent()
        self.temporal = TemporalAnalysisAgent()
        self.relationship = FeatureRelationshipAgent()
        self.dimensionality = DimensionalityReductionAgent()
        self.pca = PCAAgent()
        self.extraction = FeatureExtractionAgent()
        self.selection = FeatureSelectionAgent()
        self.planner = VisualizationPlannerAgent()
        self.executor = VisualizationExecutorAgent()
        self.validator = VisualizationValidatorAgent()
        self.insights = InsightGenerationAgent()
        self.reporter = EDAReportAgent()
        self.fallback = EDAFallbackAgent()


    def run(
        self,
        df_or_path=None,
        project_id: str = "proj_default",
        run_id: str = "run_001",
        target_column: Optional[str] = None,
        output_dir: Optional[str] = None,
        df: Optional[pd.DataFrame] = None,
        dataset_path: Optional[str] = None,
    ) -> EDAState:
        """Executes the full pipeline step-by-step with zero mock data and robust logging."""
        start_time = time.time()

        # Resolve df and dataset_path from positional arg
        if isinstance(df_or_path, pd.DataFrame):
            df = df_or_path
            dataset_path = dataset_path or "in-memory"
        elif isinstance(df_or_path, str):
            dataset_path = df_or_path
        elif df_or_path is None and df is None and dataset_path is None:
            raise ValueError("Provide either a DataFrame or a dataset_path.")

        # Use default output_dir set at construction if none given
        if output_dir is None:
            output_dir = self._default_output_dir

        dataset_path = dataset_path or "in-memory"
        logger.info(f"[EDAOrchestrator] Launching full EDA & Visualization engine for {dataset_path} (Run: {run_id})")

        state = create_initial_eda_state(
            dataset_path=dataset_path,
            project_id=project_id,
            run_id=run_id,
            target_column=target_column,
            output_dir=output_dir,
        )

        # Load dataframe once
        if df is None:
            if not Path(dataset_path).exists():
                raise FileNotFoundError(f"Dataset path {dataset_path} does not exist.")
            df = pd.read_csv(dataset_path)

        steps = [
            ("dataset_profiling", self.profiler.run, [df]),
            ("data_quality", self.quality.run, [df]),
            ("target_analysis", self.target.run, [df]),
            ("outlier_analysis", self.outlier.run, [df]),
            ("univariate_eda", self.univariate.run, [df]),
            ("bivariate_eda", self.bivariate.run, [df]),
            ("multivariate_eda", self.multivariate.run, [df]),
            ("distribution_analysis", self.distribution.run, [df]),
            ("correlation_analysis", self.correlation.run, [df]),
            ("categorical_analysis", self.categorical.run, [df]),
            ("numerical_analysis", self.numerical.run, [df]),
            ("temporal_analysis", self.temporal.run, [df]),
            ("feature_relationships", self.relationship.run, [df]),
            ("dimensionality_reduction", self.dimensionality.run, [df]),
            ("pca_analysis", self.pca.run, [df]),
            ("feature_extraction", self.extraction.run, [df]),
            ("feature_selection", self.selection.run, [df]),
            ("visualization_planning", self.planner.run, []),
            ("visualization_execution", self.executor.run, [df]),
            ("visualization_validation", self.validator.run, []),
            ("insight_generation", self.insights.run, []),
            ("eda_reporting", self.reporter.run, []),
        ]

        for step_name, agent_fn, extra_args in steps:
            t0 = time.time()
            try:
                state["current_step"] = step_name
                state = agent_fn(state, *extra_args)
                elapsed = time.time() - t0
                logger.debug(f"[EDAOrchestrator] Step '{step_name}' completed in {elapsed:.2f}s.")
            except Exception as step_exc:
                logger.error(f"[EDAOrchestrator] Exception in '{step_name}': {step_exc}")
                state = self.fallback.run(state, step_name, step_exc)

        total_elapsed = round(time.time() - start_time, 2)
        state["total_execution_time_seconds"] = total_elapsed
        logger.info(f"[EDAOrchestrator] Full EDA pipeline completed in {total_elapsed}s. Generated {len(state.get('visualization_results', []))} visual artifacts.")
        return state


def build_eda_langgraph():
    """Builds a LangGraph StateGraph representation of the EDA workflow."""
    try:
        from langgraph.graph import StateGraph, START, END

        workflow = StateGraph(EDAState)
        orchestrator = EDAOrchestrator()

        workflow.add_node("dataset_profiler", lambda s: orchestrator.profiler.run(s))
        workflow.add_node("data_quality", lambda s: orchestrator.quality.run(s))
        workflow.add_node("target_analysis", lambda s: orchestrator.target.run(s))
        workflow.add_node("outlier_analysis", lambda s: orchestrator.outlier.run(s))
        workflow.add_node("univariate_eda", lambda s: orchestrator.univariate.run(s))
        workflow.add_node("bivariate_eda", lambda s: orchestrator.bivariate.run(s))
        workflow.add_node("multivariate_eda", lambda s: orchestrator.multivariate.run(s))
        workflow.add_node("distribution_analysis", lambda s: orchestrator.distribution.run(s))
        workflow.add_node("correlation_analysis", lambda s: orchestrator.correlation.run(s))
        workflow.add_node("categorical_analysis", lambda s: orchestrator.categorical.run(s))
        workflow.add_node("numerical_analysis", lambda s: orchestrator.numerical.run(s))
        workflow.add_node("temporal_analysis", lambda s: orchestrator.temporal.run(s))
        workflow.add_node("feature_relationships", lambda s: orchestrator.relationship.run(s))
        workflow.add_node("dimensionality_reduction", lambda s: orchestrator.dimensionality.run(s))
        workflow.add_node("pca_analysis", lambda s: orchestrator.pca.run(s))
        workflow.add_node("feature_extraction", lambda s: orchestrator.extraction.run(s))
        workflow.add_node("feature_selection", lambda s: orchestrator.selection.run(s))
        workflow.add_node("visualization_planner", lambda s: orchestrator.planner.run(s))
        workflow.add_node("visualization_executor", lambda s: orchestrator.executor.run(s))
        workflow.add_node("visualization_validator", lambda s: orchestrator.validator.run(s))
        workflow.add_node("insight_generation", lambda s: orchestrator.insights.run(s))
        workflow.add_node("eda_report", lambda s: orchestrator.reporter.run(s))

        # Linear chain with conditional fallbacks
        workflow.add_edge(START, "dataset_profiler")
        workflow.add_edge("dataset_profiler", "data_quality")
        workflow.add_edge("data_quality", "target_analysis")
        workflow.add_edge("target_analysis", "outlier_analysis")
        workflow.add_edge("outlier_analysis", "univariate_eda")
        workflow.add_edge("univariate_eda", "bivariate_eda")
        workflow.add_edge("bivariate_eda", "multivariate_eda")
        workflow.add_edge("multivariate_eda", "distribution_analysis")
        workflow.add_edge("distribution_analysis", "correlation_analysis")
        workflow.add_edge("correlation_analysis", "categorical_analysis")
        workflow.add_edge("categorical_analysis", "numerical_analysis")
        workflow.add_edge("numerical_analysis", "temporal_analysis")
        workflow.add_edge("temporal_analysis", "feature_relationships")
        workflow.add_edge("feature_relationships", "dimensionality_reduction")
        workflow.add_edge("dimensionality_reduction", "pca_analysis")
        workflow.add_edge("pca_analysis", "feature_extraction")
        workflow.add_edge("feature_extraction", "feature_selection")
        workflow.add_edge("feature_selection", "visualization_planner")
        workflow.add_edge("visualization_planner", "visualization_executor")
        workflow.add_edge("visualization_executor", "visualization_validator")
        workflow.add_edge("visualization_validator", "insight_generation")
        workflow.add_edge("insight_generation", "eda_report")
        workflow.add_edge("eda_report", END)

        return workflow.compile()
    except Exception as graph_err:
        logger.warning(f"LangGraph compile note: {graph_err}")
        return None
