"""
DataWise AI — Master Agents Package (Master Spec Section 6)
Exports all 35 dedicated, strongly-typed agents with on-demand lazy loading:
  - supervisor_agent
  - dataset_ingestion_agent
  - dataset_profiling_agent
  - data_quality_agent
  - exploratory_analysis_agent
  - outlier_analysis_agent
  - missing_value_agent
  - duplicate_detection_agent
  - data_type_agent
  - target_detection_agent
  - feature_analysis_agent
  - feature_engineering_agent
  - feature_selection_agent
  - leakage_detection_agent
  - preprocessing_strategy_agent
  - preprocessing_execution_agent
  - visualization_agent
  - problem_type_agent
  - model_selection_agent
  - baseline_training_agent
  - cross_validation_agent
  - hyperparameter_optimization_agent
  - model_comparison_agent
  - overfitting_detection_agent
  - underfitting_detection_agent
  - robustness_agent
  - explainability_agent
  - model_registry_agent
  - notebook_generation_agent
  - report_generation_agent
  - deployment_agent
  - prediction_agent
  - monitoring_agent
  - drift_detection_agent
  - retraining_agent
"""

from __future__ import annotations

import importlib
from typing import Any

from .base import BaseAgent, AgentInput, AgentOutput

_AGENT_MAP = {
    # 35 Canonical Master Agents (Section 6)
    "SupervisorAgent": ("agents.supervisor_agent.agent", "SupervisorAgent"),
    "DatasetIngestionAgent": ("agents.dataset_ingestion_agent.agent", "DatasetIngestionAgent"),
    "DatasetProfilingAgent": ("agents.dataset_profiling_agent.agent", "DatasetProfilingAgent"),
    "DataQualityAgent": ("agents.data_quality_agent.agent", "DataQualityAgent"),
    "ExploratoryAnalysisAgent": ("agents.exploratory_analysis_agent.agent", "ExploratoryAnalysisAgent"),
    "OutlierAnalysisAgent": ("agents.outlier_analysis_agent.agent", "OutlierAnalysisAgent"),
    "MissingValueAgent": ("agents.missing_value_agent.agent", "MissingValueAgent"),
    "DuplicateDetectionAgent": ("agents.duplicate_detection_agent.agent", "DuplicateDetectionAgent"),
    "DataTypeAgent": ("agents.data_type_agent.agent", "DataTypeAgent"),
    "TargetDetectionAgent": ("agents.target_detection_agent.agent", "TargetDetectionAgent"),
    "FeatureAnalysisAgent": ("agents.feature_analysis_agent.agent", "FeatureAnalysisAgent"),
    "FeatureEngineeringAgent": ("agents.feature_engineering_agent.agent", "FeatureEngineeringAgent"),
    "FeatureSelectionAgent": ("agents.feature_selection_agent.agent", "FeatureSelectionAgent"),
    "LeakageDetectionAgent": ("agents.leakage_detection_agent.agent", "LeakageDetectionAgent"),
    "PreprocessingStrategyAgent": ("agents.preprocessing_strategy_agent.agent", "PreprocessingStrategyAgent"),
    "PreprocessingExecutionAgent": ("agents.preprocessing_execution_agent.agent", "PreprocessingExecutionAgent"),
    "VisualizationAgent": ("agents.visualization_agent.agent", "VisualizationAgent"),
    "ProblemTypeAgent": ("agents.problem_type_agent.agent", "ProblemTypeAgent"),
    "ModelSelectionAgent": ("agents.model_selection_agent.agent", "ModelSelectionAgent"),
    "BaselineTrainingAgent": ("agents.baseline_training_agent.agent", "BaselineTrainingAgent"),
    "CrossValidationAgent": ("agents.cross_validation_agent.agent", "CrossValidationAgent"),
    "HyperparameterOptimizationAgent": ("agents.hyperparameter_optimization_agent.agent", "HyperparameterOptimizationAgent"),
    "ModelComparisonAgent": ("agents.model_comparison_agent.agent", "ModelComparisonAgent"),
    "OverfittingDetectionAgent": ("agents.overfitting_detection_agent.agent", "OverfittingDetectionAgent"),
    "UnderfittingDetectionAgent": ("agents.underfitting_detection_agent.agent", "UnderfittingDetectionAgent"),
    "RobustnessAgent": ("agents.robustness_agent.agent", "RobustnessAgent"),
    "ExplainabilityAgent": ("agents.explainability_agent.agent", "ExplainabilityAgent"),
    "ModelRegistryAgent": ("agents.model_registry_agent.agent", "ModelRegistryAgent"),
    "NotebookGenerationAgent": ("agents.notebook_generation_agent.agent", "NotebookGenerationAgent"),
    "ReportGenerationAgent": ("agents.report_generation_agent.agent", "ReportGenerationAgent"),
    "DeploymentAgent": ("agents.deployment_agent.agent", "DeploymentAgent"),
    "PredictionAgent": ("agents.prediction_agent.agent", "PredictionAgent"),
    "MonitoringAgent": ("agents.monitoring_agent.agent", "MonitoringAgent"),
    "DriftDetectionAgent": ("agents.drift_detection_agent.agent", "DriftDetectionAgent"),
    "RetrainingAgent": ("agents.retraining_agent.agent", "RetrainingAgent"),
    "ImbalanceAgent": ("agents.imbalance_agent.agent", "ImbalanceAgent"),
    "ThresholdOptimizationAgent": ("agents.threshold_optimization_agent.agent", "ThresholdOptimizationAgent"),
    "FinalModelSelectionAgent": ("agents.final_model_selection_agent.agent", "FinalModelSelectionAgent"),
    "IterativeOptimizationAgent": ("agents.iterative_optimization_agent.agent", "IterativeOptimizationAgent"),
    "PerformanceMonitoringAgent": ("agents.performance_monitoring_agent.agent", "PerformanceMonitoringAgent"),
    "AuditAgent": ("agents.audit_agent.agent", "AuditAgent"),
    "ModelCandidateAgent": ("agents.model_candidate_agent.agent", "ModelCandidateAgent"),
    "ExperimentManagerAgent": ("agents.experiment_manager_agent.agent", "ExperimentManagerAgent"),
    "DataTypeDetectionAgent": ("agents.data_type_detection_agent.agent", "DataTypeDetectionAgent"),
    "OverfittingAgent": ("agents.overfitting_agent.agent", "OverfittingAgent"),
    "UnderfittingAgent": ("agents.underfitting_agent.agent", "UnderfittingAgent"),

    # Backward Compatibility Aliases
    "IntakeAgent": ("agents.dataset_ingestion_agent.agent", "DatasetIngestionAgent"),
    "ProfilingAgent": ("agents.dataset_profiling_agent.agent", "DatasetProfilingAgent"),
    "OutlierAgent": ("agents.outlier_analysis_agent.agent", "OutlierAnalysisAgent"),
    "MissingValuesAgent": ("agents.missing_value_agent.agent", "MissingValueAgent"),
    "EncodingAgent": ("agents.preprocessing_strategy_agent.agent", "PreprocessingStrategyAgent"),
    "ScalingAgent": ("agents.preprocessing_execution_agent.agent", "PreprocessingExecutionAgent"),
    "TransformationAgent": ("agents.transformation.agent", "TransformationAgent"),
    "HyperparameterTuningAgent": ("agents.hyperparameter_optimization_agent.agent", "HyperparameterOptimizationAgent"),
    "EvaluationAgent": ("agents.evaluation.agent", "EvaluationAgent"),
    "ArtifactGenerationAgent": ("agents.model_registry_agent.agent", "ModelRegistryAgent"),
    "TrainingAgent": ("agents.baseline_training_agent.agent", "BaselineTrainingAgent"),
    "ArtifactValidationAgent": ("agents.artifact_validation_agent", "ArtifactValidationAgent"),
}

__all__ = [
    "BaseAgent",
    "AgentInput",
    "AgentOutput",
    *_AGENT_MAP.keys(),
]


def __getattr__(name: str) -> Any:
    if name in _AGENT_MAP:
        module_path, class_name = _AGENT_MAP[name]
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    raise AttributeError(f"module 'agents' has no attribute '{name}'")
