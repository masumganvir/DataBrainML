"""
DataWise AI — Specialized Multi-Agent Domain Subsystem
Exports all domain agents and the central MultiAgentCoordinator.
Organized into dedicated agent folders per domain task type.
"""

from app.agents.artifacts import ArtifactManagerAgent
from app.agents.base import BaseAgent
from app.agents.coordinator import MultiAgentCoordinator, multi_agent_coordinator
from app.agents.evaluation import EvaluationAgent
from app.agents.explainability import ExplainabilityAgent
from app.agents.feature_engineering import FeatureEngineeringAgent
from app.agents.feature_selection import FeatureSelectionAgent
from app.agents.governance import HumanApprovalNode
from app.agents.intake import IntakeAgent
from app.agents.ml_readiness import MLReadinessAgent
from app.agents.ml_recommendation import MLRecommendationAgent
from app.agents.notebook import NotebookAgent
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
from app.agents.training import TrainingAgent
from app.agents.visualization import VisualizationAgent

__all__ = [
    "BaseAgent",
    "IntakeAgent",
    "ProfilingAgent",
    "QualityAgent",
    "OutlierAgent",
    "VisualizationAgent",
    "PreprocessingAgent",
    "MissingValueAgent",
    "EncodingAgent",
    "ScalingAgent",
    "TransformationAgent",
    "FeatureEngineeringAgent",
    "FeatureSelectionAgent",
    "MLReadinessAgent",
    "PipelineBuilderAgent",
    "MLRecommendationAgent",
    "TrainingAgent",
    "EvaluationAgent",
    "ExplainabilityAgent",
    "NotebookAgent",
    "ReportAgent",
    "ArtifactManagerAgent",
    "HumanApprovalNode",
    "MultiAgentCoordinator",
    "multi_agent_coordinator",
]
