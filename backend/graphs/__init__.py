"""
DataWise AI — Central LangGraph Architecture (Section 5)
Exports Master SupervisorGraph and all 9 Subgraphs.
"""

from graphs.state import AgentState, create_initial_agent_state
from graphs.supervisor_graph import build_supervisor_graph, SupervisorGraph
from graphs.data_analysis_graph import build_data_analysis_graph
from graphs.preprocessing_graph import build_preprocessing_graph
from graphs.feature_engineering_graph import build_feature_engineering_graph
from graphs.model_selection_graph import build_model_selection_graph
from graphs.training_graph import build_training_graph
from graphs.evaluation_graph import build_evaluation_graph
from graphs.deployment_graph import build_deployment_graph
from graphs.monitoring_graph import build_monitoring_graph
from graphs.retraining_graph import build_retraining_graph
from graphs.optimization_graph import build_optimization_graph
from graphs.master_graph import build_master_graph, execute_master_workflow
from graphs.ingestion_graph import ingestion_subgraph, create_ingestion_graph
from graphs.online_learning_graph import online_learning_subgraph, create_online_learning_graph
from graphs.analysis_graph import build_analysis_graph
from graphs.main_graph import build_main_graph

from graphs.recovery_graph import build_recovery_graph

DataAnalysisGraph = build_data_analysis_graph
PreprocessingGraph = build_preprocessing_graph
FeatureEngineeringGraph = build_feature_engineering_graph
ModelSelectionGraph = build_model_selection_graph
TrainingGraph = build_training_graph
OptimizationGraph = build_optimization_graph
EvaluationGraph = build_evaluation_graph
DeploymentGraph = build_deployment_graph
MonitoringGraph = build_monitoring_graph
RetrainingGraph = build_retraining_graph
IngestionGraph = create_ingestion_graph
OnlineLearningGraph = create_online_learning_graph
MainGraph = build_main_graph
RecoveryGraph = build_recovery_graph

__all__ = [
    "AgentState",
    "create_initial_agent_state",
    "SupervisorGraph",
    "build_supervisor_graph",
    "DataAnalysisGraph",
    "build_data_analysis_graph",
    "PreprocessingGraph",
    "build_preprocessing_graph",
    "FeatureEngineeringGraph",
    "build_feature_engineering_graph",
    "ModelSelectionGraph",
    "build_model_selection_graph",
    "TrainingGraph",
    "build_training_graph",
    "OptimizationGraph",
    "build_optimization_graph",
    "EvaluationGraph",
    "build_evaluation_graph",
    "DeploymentGraph",
    "build_deployment_graph",
    "MonitoringGraph",
    "build_monitoring_graph",
    "RetrainingGraph",
    "build_retraining_graph",
    "build_master_graph",
    "execute_master_workflow",
    "RecoveryGraph",
    "build_recovery_graph",
]

