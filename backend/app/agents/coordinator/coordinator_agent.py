"""
DataWise AI — Multi-Agent Coordinator & Supervisor
Manages specialized domain agents, orchestrates intent routing, and dispatches tasks.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.agents.artifacts.artifact_agent import ArtifactManagerAgent
from app.agents.base.base_agent import BaseAgent
from app.agents.evaluation.evaluation_agent import EvaluationAgent
from app.agents.explainability.explainability_agent import ExplainabilityAgent
from app.agents.feature_engineering.feature_engineering_agent import FeatureEngineeringAgent
from app.agents.feature_selection.feature_selection_agent import FeatureSelectionAgent
from app.agents.governance.human_approval_node import HumanApprovalNode
from app.agents.intake.intake_agent import IntakeAgent
from app.agents.ml_readiness.ml_readiness_agent import MLReadinessAgent
from app.agents.ml_recommendation.ml_recommendation_agent import MLRecommendationAgent
from app.agents.notebook.notebook_agent import NotebookAgent
from app.agents.outliers.outlier_agent import OutlierAgent
from app.agents.pipeline_builder.pipeline_builder_agent import PipelineBuilderAgent
from app.agents.preprocessing.preprocessing_agent import (
    EncodingAgent,
    MissingValueAgent,
    PreprocessingAgent,
    ScalingAgent,
    TransformationAgent,
)
from app.agents.profiling.profiling_agent import ProfilingAgent
from app.agents.quality.quality_agent import QualityAgent
from app.agents.reporting.report_agent import ReportAgent
from app.agents.training.training_agent import TrainingAgent
from app.agents.visualization.visualization_agent import VisualizationAgent
from app.graph.llm_provider import LLMMessage
from app.state.data_science_state import DataScienceState


class MultiAgentCoordinator:
    """
    Central orchestrator for all specialized data science agents.
    Provides intent-based task dispatching and conversational routing.
    """

    def __init__(self) -> None:
        self.intake_agent = IntakeAgent()
        self.profiling_agent = ProfilingAgent()
        self.quality_agent = QualityAgent()
        self.outlier_agent = OutlierAgent()
        self.visualization_agent = VisualizationAgent()
        self.preprocessing_agent = PreprocessingAgent()
        self.missing_value_agent = MissingValueAgent()
        self.encoding_agent = EncodingAgent()
        self.scaling_agent = ScalingAgent()
        self.transformation_agent = TransformationAgent()
        self.feature_engineering_agent = FeatureEngineeringAgent()
        self.feature_selection_agent = FeatureSelectionAgent()
        self.ml_readiness_agent = MLReadinessAgent()
        self.pipeline_builder_agent = PipelineBuilderAgent()
        self.ml_recommendation_agent = MLRecommendationAgent()
        self.training_agent = TrainingAgent()
        self.evaluation_agent = EvaluationAgent()
        self.explainability_agent = ExplainabilityAgent()
        self.notebook_agent = NotebookAgent()
        self.artifact_agent = ArtifactManagerAgent()
        self.report_agent = ReportAgent()
        self.human_approval = HumanApprovalNode()

        self._agents_registry: Dict[str, BaseAgent] = {
            "intake": self.intake_agent,
            "profiling": self.profiling_agent,
            "quality": self.quality_agent,
            "outlier": self.outlier_agent,
            "visualization": self.visualization_agent,
            "preprocessing": self.preprocessing_agent,
            "missing_value": self.missing_value_agent,
            "encoding": self.encoding_agent,
            "scaling": self.scaling_agent,
            "transformation": self.transformation_agent,
            "feature_engineering": self.feature_engineering_agent,
            "feature_selection": self.feature_selection_agent,
            "ml_readiness": self.ml_readiness_agent,
            "pipeline_builder": self.pipeline_builder_agent,
            "ml_recommendation": self.ml_recommendation_agent,
            "training": self.training_agent,
            "evaluation": self.evaluation_agent,
            "explainability": self.explainability_agent,
            "notebook": self.notebook_agent,
            "report": self.report_agent,
            "artifacts": self.artifact_agent,
        }

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Fetch an agent by its key identifier."""
        return self._agents_registry.get(agent_id.lower())

    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents and their specialization."""
        return [
            {
                "id": k,
                "name": v.name,
                "role": v.role,
                "description": v.description,
            }
            for k, v in self._agents_registry.items()
        ]

    def route_query(self, query: str, current_stage: Optional[str] = None) -> BaseAgent:
        """
        Determines the most qualified agent to handle a specific user question.
        Uses keyword intent matching with fallback to current workflow stage.
        """
        q = query.lower()

        # 0. Jupyter Notebook Generation
        if any(w in q for w in ["notebook", "jupyter", ".ipynb", "colab"]):
            return self.notebook_agent

        # 1. Artifacts & ZIP Package Downloads
        if any(w in q for w in ["bundle", "download zip", "export model", "joblib", "inference script", "package", "download all"]):
            return self.artifact_agent

        # 2. Model Training & Cross-Validation
        if any(w in q for w in ["train", "training", "fit model", "cross-validation", "cv fold", "run models"]):
            return self.training_agent

        # 3. Model Evaluation & Comparison
        if any(w in q for w in ["evaluate", "evaluation", "compare models", "model comparison", "shift", "production ready", "readiness audit"]):
            return self.evaluation_agent

        # 4. Feature Selection
        if any(w in q for w in ["select feature", "feature selection", "prune", "drop low variance", "mutual info"]):
            return self.feature_selection_agent

        # 5. Explainability & Limitations
        if any(w in q for w in ["explain", "permutation", "limitations", "interpret", "feature importance"]):
            return self.explainability_agent

        # 5. Pipeline & Code Generation
        if any(w in q for w in ["code", "pipeline", "columntransformer", "sklearn", "script", "export python"]):
            return self.pipeline_builder_agent

        # 6. ML Recommendations & Algorithms
        if any(w in q for w in ["model", "algorithm", "xgboost", "random forest", "lightgbm", "hyperparameter", "accuracy", "roc", "f1"]):
            return self.ml_recommendation_agent

        # 7. Leakage & Target Detection
        if any(w in q for w in ["target", "label", "leakage", "readiness", "task type", "classification or regression"]):
            return self.ml_readiness_agent

        # 8. Feature Engineering
        if any(w in q for w in ["engineer", "interaction", "polynomial", "datetime", "create feature", "new feature", "ratio"]):
            return self.feature_engineering_agent

        # 10. Preprocessing, Encoding & Scaling
        if any(w in q for w in ["encode", "scaling", "standardscaler", "onehot", "impute", "imputation", "normalize", "preprocess"]):
            return self.preprocessing_agent

        # 11. Outliers & Anomalies
        if any(w in q for w in ["outlier", "anomaly", "anomalies", "iqr", "isolation forest", "extreme value", "winsorize"]):
            return self.outlier_agent

        # 12. Visualizations, Distributions & Correlations
        if any(w in q for w in ["plot", "chart", "distribution", "correlation", "heatmap", "histogram", "skew", "kurtosis"]):
            return self.visualization_agent

        # 13. Quality, Missing Values & Duplicates
        if any(w in q for w in ["missing", "null", "nan", "duplicate", "clean", "hygiene", "quality"]):
            return self.quality_agent

        # 14. Reports & Documentation
        if any(w in q for w in ["report", "pdf", "html", "summary document"]):
            return self.report_agent

        # 15. Profiling & Columns
        if any(w in q for w in ["profile", "column", "datatype", "dtype", "unique", "cardinality", "overview"]):
            return self.profiling_agent

        # Fallback based on stage
        stage_map: Dict[str, BaseAgent] = {
            "PROFILE": self.profiling_agent,
            "QUALITY": self.quality_agent,
            "OUTLIERS": self.outlier_agent,
            "DISTRIBUTIONS": self.visualization_agent,
            "CORRELATIONS": self.visualization_agent,
            "FEATURE_ENGINEERING": self.feature_engineering_agent,
            "FEATURE_SELECTION": self.feature_selection_agent,
            "TARGET_DETECTION": self.ml_readiness_agent,
            "LEAKAGE_CHECK": self.ml_readiness_agent,
            "PIPELINE_BUILDING": self.pipeline_builder_agent,
            "ML_RECOMMENDATION": self.ml_recommendation_agent,
            "TRAINING": self.training_agent,
            "EVALUATION": self.evaluation_agent,
            "EXPLAINABILITY": self.explainability_agent,
            "NOTEBOOK_GENERATION": self.notebook_agent,
            "ARTIFACT_PACKAGING": self.artifact_agent,
            "COMPLETE": self.report_agent,
        }

        if current_stage and current_stage in stage_map:
            return stage_map[current_stage]

        return self.profiling_agent

    async def dispatch_chat(
        self,
        query: str,
        state: Optional[DataScienceState] = None,
        history: Optional[List[LLMMessage]] = None,
        forced_agent_id: Optional[str] = None,
    ) -> Tuple[BaseAgent, str]:
        """
        Routes the user's message to the appropriate domain agent, executes response,
        and attaches domain badges.
        """
        agent = self.get_agent(forced_agent_id) if forced_agent_id else None
        if not agent:
            current_stage = state.get("current_stage") if state else None
            agent = self.route_query(query, current_stage=current_stage)

        logger.info(f"[Coordinator] Dispatched query to agent: {agent.name}")
        response = await agent.respond(query=query, state=state, history=history)
        
        # Add badge if not already present
        if not response.startswith(f"🤖 **[{agent.name}]"):
            response = f"🤖 **[{agent.name} — {agent.role}]**\n\n{response}"

        return agent, response


# Global coordinator singleton
multi_agent_coordinator = MultiAgentCoordinator()
