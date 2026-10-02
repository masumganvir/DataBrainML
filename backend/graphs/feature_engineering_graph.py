"""
DataWise AI — Feature Engineering Subgraph (LangGraph Section 5)
Orchestrates candidate feature generation, cross-validation-aware feature selection,
and rigorous data leakage detection.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.feature_engineering import FeatureEngineeringAgent
from agents.feature_selection import FeatureSelectionAgent
from agents.leakage_detection import LeakageDetectionAgent


def feature_engineering_node(state: AgentState) -> AgentState:
    logger.info("[FeatureEngineeringGraph] Running Feature Engineering Node")
    agent = FeatureEngineeringAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={
            "target_column": state.get("target_column"),
            "datetime_columns": state.get("datetime_columns", []),
        },
    ))
    return {
        **state,
        "feature_engineering_plan": out.data.get("candidate_features", []),
        "current_step": "feature_selection",
        "completed_steps": [*state.get("completed_steps", []), "feature_engineering"],
    }


def feature_selection_node(state: AgentState) -> AgentState:
    logger.info("[FeatureEngineeringGraph] Running Feature Selection Node")
    agent = FeatureSelectionAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "feature_selection_result": out.data.get("selected_features", []),
        "current_step": "leakage_detection",
        "completed_steps": [*state.get("completed_steps", []), "feature_selection"],
    }


def leakage_detection_node(state: AgentState) -> AgentState:
    logger.info("[FeatureEngineeringGraph] Running Leakage Detection Node")
    agent = LeakageDetectionAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={"target_column": state.get("target_column")},
    ))
    report = out.data.get("leakage_report", {})
    return {
        **state,
        "leakage_report": report,
        "current_step": "feature_engineering_complete",
        "completed_steps": [*state.get("completed_steps", []), "leakage_detection"],
    }


def build_feature_engineering_graph() -> StateGraph:
    """Constructs the compiled FeatureEngineeringGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("feature_engineering", feature_engineering_node)
    graph.add_node("feature_selection", feature_selection_node)
    graph.add_node("leakage_detection", leakage_detection_node)

    graph.set_entry_point("feature_engineering")
    graph.add_edge("feature_engineering", "feature_selection")
    graph.add_edge("feature_selection", "leakage_detection")
    graph.add_edge("leakage_detection", END)

    return graph.compile()
