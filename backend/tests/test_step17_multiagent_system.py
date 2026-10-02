"""
DataWise AI — Comprehensive Multi-Agent System Tests
Validates the specialized domain agents, coordinator routing, and workflow integration.
"""

import os
import tempfile
import pandas as pd
import pytest

from app.agents.base import BaseAgent
from app.agents.coordinator import MultiAgentCoordinator, multi_agent_coordinator
from app.agents.feature_engineering import FeatureEngineeringAgent
from app.agents.feature_selection import FeatureSelectionAgent
from app.agents.intake import IntakeAgent
from app.agents.ml_readiness import MLReadinessAgent
from app.agents.ml_recommendation import MLRecommendationAgent
from app.agents.outliers import OutlierAgent
from app.agents.pipeline_builder import PipelineBuilderAgent
from app.agents.preprocessing import (
    EncodingAgent,
    MissingValueAgent,
    PreprocessingAgent,
    ScalingAgent,
    TransformationAgent,
)
from app.agents.profiling import ProfilingAgent
from app.agents.quality import QualityAgent
from app.agents.reporting import ReportAgent
from app.agents.visualization import VisualizationAgent
from app.graph.workflow import run_analysis_workflow
from app.state.data_science_state import DataScienceState


@pytest.fixture
def sample_csv_file():
    df = pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 120],  # Outlier: 120
        "income": [30000.0, 45000.0, None, 60000.0, 80000.0, 95000.0, 110000.0, 130000.0, None, 250000.0],
        "category": ["A", "B", "A", "C", "B", "A", "C", "B", "A", "C"],
        "churn": [0, 1, 0, 0, 1, 0, 1, 0, 1, 1],
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="") as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def initial_state(sample_csv_file) -> DataScienceState:
    return {
        "session_id": "test_agent_session_123",
        "dataset_path_original": sample_csv_file,
        "dataset_path_analysis": sample_csv_file,
        "row_count_original": 10,
        "column_count_original": 5,
        "current_stage": "INGEST",
        "completed_stages": [],
        "errors": [],
        "target_column": "churn",
        "task_type": "binary_classification",
        "user_decisions": [],
    }


def test_agent_registration_and_metadata():
    coordinator = MultiAgentCoordinator()
    agents = coordinator.list_agents()
    assert len(agents) >= 12

    agent_names = {a["name"] for a in agents}
    expected_agents = {
        "IntakeAgent",
        "ProfilingAgent",
        "QualityAgent",
        "OutlierAgent",
        "VisualizationAgent",
        "PreprocessingAgent",
        "FeatureEngineeringAgent",
        "FeatureSelectionAgent",
        "MLReadinessAgent",
        "PipelineBuilderAgent",
        "MLRecommendationAgent",
        "ReportAgent",
    }
    for expected in expected_agents:
        assert expected in agent_names, f"Expected agent {expected} to be registered"


def test_intake_and_profiling_agents(initial_state):
    intake = IntakeAgent()
    s1 = intake.run(initial_state)
    assert "INGEST" in s1["completed_stages"]
    assert s1["row_count_current"] == 10

    profiler = ProfilingAgent()
    s2 = profiler.run(s1)
    assert "PROFILE" in s2["completed_stages"]
    assert len(s2["column_profiles"]) == 5
    assert "age" in s2["numerical_columns"]
    assert "category" in s2["categorical_columns"]


def test_quality_and_outlier_agents(initial_state):
    profiler = ProfilingAgent()
    s = profiler.run(initial_state)

    quality = QualityAgent()
    s_qual = quality.run(s)
    assert "QUALITY" in s_qual["completed_stages"]
    assert len(s_qual["missing_value_report"]) > 0

    outlier = OutlierAgent()
    s_out = outlier.run(s_qual)
    assert "OUTLIERS" in s_out["completed_stages"]
    assert len(s_out["outlier_report"]) > 0


def test_preprocessing_and_subagents(initial_state):
    profiler = ProfilingAgent()
    s = profiler.run(initial_state)

    prep = PreprocessingAgent()
    s_prep = prep.run(s)
    assert "encoding_plan" in s_prep
    assert "scaling_plan" in s_prep

    # Subagent existence checks
    assert isinstance(MissingValueAgent(), BaseAgent)
    assert isinstance(EncodingAgent(), BaseAgent)
    assert isinstance(ScalingAgent(), BaseAgent)
    assert isinstance(TransformationAgent(), BaseAgent)


def test_feature_engineering_and_selection_agents(initial_state):
    profiler = ProfilingAgent()
    s = profiler.run(initial_state)

    fe_agent = FeatureEngineeringAgent()
    s_fe = fe_agent.run(s)
    assert "FEATURE_ENGINEERING" in s_fe["completed_stages"]
    assert "feature_engineering_plan" in s_fe

    fs_agent = FeatureSelectionAgent()
    s_fs = fs_agent.run(s)
    assert "FEATURE_SELECTION" in s_fs["completed_stages"]
    assert "selected_features" in s_fs


def test_pipeline_and_ml_recommendation_agents(initial_state):
    profiler = ProfilingAgent()
    s = profiler.run(initial_state)

    pb_agent = PipelineBuilderAgent()
    s_pb = pb_agent.run(s)
    assert "PIPELINE_BUILDING" in s_pb["completed_stages"]
    assert "ColumnTransformer" in s_pb["generated_pipeline_code"]

    ml_agent = MLRecommendationAgent()
    s_ml = ml_agent.run(s_pb)
    assert "ML_RECOMMENDATION" in s_ml["completed_stages"]
    assert len(s_ml["model_recommendations"]) > 0
    assert s_ml["ml_readiness_score"] is not None


def test_report_agent(initial_state):
    profiler = ProfilingAgent()
    s = profiler.run(initial_state)

    rep_agent = ReportAgent()
    md_report = rep_agent.generate_markdown(s)
    assert "# DataWise AI" in md_report or "Dataset" in md_report

    html_report = rep_agent.generate_html(s)
    assert "<html" in html_report.lower()


def test_coordinator_intent_routing():
    coordinator = MultiAgentCoordinator()

    # Route code / pipeline
    a1 = coordinator.route_query("Can you generate the scikit-learn pipeline code?")
    assert a1.name == "PipelineBuilderAgent"

    # Route ML models
    a2 = coordinator.route_query("Which ML algorithms like XGBoost or Random Forest should I use?")
    assert a2.name == "MLRecommendationAgent"

    # Route Outliers
    a3 = coordinator.route_query("Are there severe outliers or anomalies in the income column?")
    assert a3.name == "OutlierAgent"

    # Route Missing data
    a4 = coordinator.route_query("How many missing null values are there?")
    assert a4.name == "QualityAgent"

    # Route Feature selection
    a5 = coordinator.route_query("What features should we select and prune based on importance?")
    assert a5.name == "FeatureSelectionAgent"

    # Route Feature engineering
    a6 = coordinator.route_query("Can you engineer new interaction features from these variables?")
    assert a6.name == "FeatureEngineeringAgent"

    # Route Plots & Distributions
    a7 = coordinator.route_query("Show me a correlation heatmap and distribution plot")
    assert a7.name == "VisualizationAgent"


@pytest.mark.asyncio
async def test_coordinator_dispatch_chat(initial_state):
    agent, reply = await multi_agent_coordinator.dispatch_chat(
        query="What outliers are present in this data?",
        state=initial_state,
    )
    assert agent.name == "OutlierAgent"
    assert "OutlierAgent" in reply


@pytest.mark.asyncio
async def test_workflow_execution_with_agents(initial_state):
    final_state = await run_analysis_workflow(initial_state)
    assert "PROFILE" in final_state.get("completed_stages", [])
    assert "QUALITY" in final_state.get("completed_stages", [])
