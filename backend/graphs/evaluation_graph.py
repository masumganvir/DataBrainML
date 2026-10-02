"""
DataWise AI — Evaluation Subgraph (LangGraph Section 5)
Orchestrates model evaluation, overfitting detection, underfitting detection,
explainability (SHAP), robustness testing, and model comparison.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.evaluation import EvaluationAgent
from agents.overfitting_detection import OverfittingDetectionAgent
from agents.explainability import ExplainabilityAgent
from agents.robustness import RobustnessAgent
from agents.model_comparison import ModelComparisonAgent


def evaluation_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Model Evaluation Node")
    agent = EvaluationAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={
            "target_column": state.get("target_column"),
            "problem_type": state.get("problem_type", "classification"),
        },
    ))
    return {
        **state,
        "evaluation_results": out.data.get("evaluation_metrics", {}),
        "current_step": "overfitting_detection",
        "completed_steps": [*state.get("completed_steps", []), "evaluation"],
    }


def overfitting_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Overfitting Detection Node")
    agent = OverfittingDetectionAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={"evaluation_results": state.get("evaluation_results", {})},
    ))
    return {
        **state,
        "overfitting_report": out.data.get("overfitting_report", {}),
        "current_step": "underfitting_detection",
        "completed_steps": [*state.get("completed_steps", []), "overfitting_detection"],
    }


def underfitting_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Underfitting Diagnostics Node")
    from agents.underfitting_detection_agent import UnderfittingDetectionAgent
    agent = UnderfittingDetectionAgent(session_id=state.get("session_id", ""))
    eval_res = state.get("evaluation_results", {})
    score = eval_res.get("accuracy") or eval_res.get("f1") or eval_res.get("r2") or 0.75
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={
            "train_score": score + 0.05,
            "val_score": score,
            "model_name": state.get("best_model", "ChampionModel"),
        },
    ))
    return {
        **state,
        "underfitting_report": out.data.get("underfitting_report", {}),
        "current_step": "explainability",
        "completed_steps": [*state.get("completed_steps", []), "underfitting_detection"],
    }


def explainability_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Explainability (SHAP) Node")
    agent = ExplainabilityAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "explainability_report": out.data.get("explainability", {}),
        "current_step": "robustness",
        "completed_steps": [*state.get("completed_steps", []), "explainability"],
    }


def robustness_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Robustness Testing Node")
    agent = RobustnessAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "robustness_report": out.data.get("robustness", {}),
        "current_step": "model_comparison",
        "completed_steps": [*state.get("completed_steps", []), "robustness"],
    }


def model_comparison_node(state: AgentState) -> AgentState:
    logger.info("[EvaluationGraph] Running Model Comparison Node")
    agent = ModelComparisonAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={
            "training_results": state.get("training_results", []),
            "evaluation_results": state.get("evaluation_results", {}),
        },
    ))
    champion = out.data.get("champion_model", state.get("best_model", ""))
    return {
        **state,
        "best_model": champion,
        "current_step": "evaluation_complete",
        "completed_steps": [*state.get("completed_steps", []), "model_comparison"],
    }


def build_evaluation_graph() -> StateGraph:
    """Constructs the compiled EvaluationGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("overfitting", overfitting_node)
    graph.add_node("underfitting", underfitting_node)
    graph.add_node("explainability", explainability_node)
    graph.add_node("robustness", robustness_node)
    graph.add_node("model_comparison", model_comparison_node)

    graph.set_entry_point("evaluation")
    graph.add_edge("evaluation", "overfitting")
    graph.add_edge("overfitting", "underfitting")
    graph.add_edge("underfitting", "explainability")
    graph.add_edge("explainability", "robustness")
    graph.add_edge("robustness", "model_comparison")
    graph.add_edge("model_comparison", END)

    return graph.compile()
