"""
DataWise AI — Training & AutoML Subgraph
Modular LangGraph StateGraph governing ML problem detection, algorithm selection,
pipeline construction, cross-validation, Optuna tuning, evaluation, overfitting diagnostics,
explainability (SHAP), robustness testing, model comparison, artifact packaging, and deployment.
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.problem_type import ProblemTypeAgent
from agents.model_selection import ModelSelectionAgent
from agents.training import TrainingAgent
from agents.hyperparameter_tuning import HyperparameterTuningAgent
from agents.evaluation import EvaluationAgent
from agents.overfitting_detection import OverfittingDetectionAgent
from agents.explainability import ExplainabilityAgent
from agents.robustness import RobustnessAgent
from agents.model_comparison import ModelComparisonAgent
from agents.artifact_generation import ArtifactGenerationAgent
from agents.deployment import DeploymentAgent


# ─── Node Functions ────────────────────────────────────────────────────────────

def problem_type_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Problem Type Detection Node")
    agent = ProblemTypeAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    p_type = out.data.get("problem_type", "classification")
    return {
        **state,
        "problem_type": p_type,
        "current_step": "model_selection",
        "completed_steps": [*state.get("completed_steps", []), "problem_type"],
    }


def model_selection_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Model Selection Node")
    agent = ModelSelectionAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={"problem_type": state.get("problem_type", "classification")},
    ))
    return {
        **state,
        "candidate_models": out.data.get("candidate_models", []),
        "current_step": "training",
        "completed_steps": [*state.get("completed_steps", []), "model_selection"],
    }


def training_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Candidate Model Training Node")
    agent = TrainingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={
            "target_column": state.get("target_column"),
            "task_type": state.get("problem_type", "classification"),
            "cv_folds": 3,
        },
    ))
    return {
        **state,
        "training_results": out.data.get("training_results", []),
        "best_model": out.data.get("champion_model", ""),
        "current_step": "hyperparameter_tuning",
        "completed_steps": [*state.get("completed_steps", []), "training"],
    }


def hyperparameter_tuning_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Hyperparameter Tuning Node")
    agent = HyperparameterTuningAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={
            "target_column": state.get("target_column"),
            "task_type": state.get("problem_type", "classification"),
            "model_name": state.get("best_model", "RandomForestClassifier"),
            "n_trials": 10,
        },
    ))
    return {
        **state,
        "hyperparameter_results": out.data,
        "current_step": "evaluation",
        "completed_steps": [*state.get("completed_steps", []), "hyperparameter_tuning"],
    }


def evaluation_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Evaluation Node")
    agent = EvaluationAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={"task_type": state.get("problem_type", "classification")},
    ))
    return {
        **state,
        "evaluation_results": out.data.get("evaluation_metrics", {}),
        "current_step": "overfitting_detection",
        "completed_steps": [*state.get("completed_steps", []), "evaluation"],
    }


def overfitting_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Overfitting Detection Node")
    agent = OverfittingDetectionAgent(session_id=state["session_id"])
    top_model = state.get("training_results", [{}])[0] if state.get("training_results") else {}
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "train_score": top_model.get("train_score", 0.90),
            "cv_score": top_model.get("cv_mean", 0.85),
            "test_score": top_model.get("test_score", 0.84),
        },
    ))
    return {
        **state,
        "overfitting_report": out.data,
        "current_step": "explainability",
        "completed_steps": [*state.get("completed_steps", []), "overfitting_detection"],
    }


def explainability_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Explainability Node (SHAP)")
    agent = ExplainabilityAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "explainability_report": out.data,
        "current_step": "robustness",
        "completed_steps": [*state.get("completed_steps", []), "explainability"],
    }


def robustness_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Robustness Node")
    agent = RobustnessAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "robustness_report": out.data,
        "current_step": "model_comparison",
        "completed_steps": [*state.get("completed_steps", []), "robustness"],
    }


def model_comparison_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Model Comparison Node")
    agent = ModelComparisonAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={"trained_models": state.get("training_results", [])},
    ))
    champ = out.data.get("champion_model_name", state.get("best_model", "Champion"))
    return {
        **state,
        "best_model": champ,
        "current_step": "artifact_generation",
        "completed_steps": [*state.get("completed_steps", []), "model_comparison"],
    }


def artifact_generation_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Artifact Generation Node")
    agent = ArtifactGenerationAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "champion_model": state.get("best_model"),
            "target_column": state.get("target_column"),
            "feature_names": state.get("feature_columns", []),
        },
    ))
    return {
        **state,
        "model_path": out.data.get("zip_path"),
        "notebook_path": out.data.get("bundle_directory"),
        "current_step": "deployment",
        "completed_steps": [*state.get("completed_steps", []), "artifact_generation"],
    }


def deployment_node(state: AgentState) -> AgentState:
    logger.info("[TrainingGraph] Running Deployment Node")
    agent = DeploymentAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "champion_model": state.get("best_model"),
            "feature_names": state.get("feature_columns", []),
        },
    ))
    return {
        **state,
        "deployment_status": "deployed",
        "current_step": "COMPLETE_TRAINING",
        "completed_steps": [*state.get("completed_steps", []), "deployment"],
    }


# ─── Graph Builder ─────────────────────────────────────────────────────────────

def build_training_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("problem_type", problem_type_node)
    graph.add_node("model_selection", model_selection_node)
    graph.add_node("training", training_node)
    graph.add_node("tuning", hyperparameter_tuning_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("overfitting", overfitting_node)
    graph.add_node("explainability", explainability_node)
    graph.add_node("robustness", robustness_node)
    graph.add_node("comparison", model_comparison_node)
    graph.add_node("artifacts", artifact_generation_node)
    graph.add_node("deployment", deployment_node)

    graph.set_entry_point("problem_type")
    graph.add_edge("problem_type", "model_selection")
    graph.add_edge("model_selection", "training")
    graph.add_edge("training", "tuning")
    graph.add_edge("tuning", "evaluation")
    graph.add_edge("evaluation", "overfitting")
    graph.add_edge("overfitting", "explainability")
    graph.add_edge("explainability", "robustness")
    graph.add_edge("robustness", "comparison")
    graph.add_edge("comparison", "artifacts")
    graph.add_edge("artifacts", "deployment")
    graph.add_edge("deployment", END)

    return graph.compile()
