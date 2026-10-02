"""
DataWise AI — Preprocessing Subgraph
Modular LangGraph StateGraph governing intake, profiling, quality, outlier intelligence,
missing values, encoding, scaling, transformation, feature engineering, selection, and leakage detection.
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.intake import IntakeAgent
from agents.profiling import ProfilingAgent
from agents.data_quality import DataQualityAgent
from agents.outlier import OutlierAgent
from agents.missing_values import MissingValuesAgent
from agents.encoding import EncodingAgent
from agents.scaling import ScalingAgent
from agents.transformation import TransformationAgent
from agents.feature_engineering import FeatureEngineeringAgent
from agents.feature_selection import FeatureSelectionAgent
from agents.leakage_detection import LeakageDetectionAgent


# ─── Node Functions ────────────────────────────────────────────────────────────

def intake_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Intake Node")
    agent = IntakeAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
    ))
    meta = out.data.get("metadata", {})
    return {
        **state,
        "dataset_metadata": meta,
        "current_step": "profiling",
        "completed_steps": [*state.get("completed_steps", []), "intake"],
    }


def profiling_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Profiling Node")
    agent = ProfilingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
    ))
    prof = out.data.get("profile", {})
    return {
        **state,
        "dataset_profile": prof,
        "numerical_columns": prof.get("numerical_columns", []),
        "categorical_columns": prof.get("categorical_columns", []),
        "datetime_columns": prof.get("datetime_columns", []),
        "identifier_columns": prof.get("identifier_columns", []),
        "current_step": "data_quality",
        "completed_steps": [*state.get("completed_steps", []), "profiling"],
    }


def data_quality_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Data Quality Node")
    agent = DataQualityAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
    ))
    return {
        **state,
        "data_quality_report": out.data.get("quality_report", {}),
        "current_step": "outlier",
        "completed_steps": [*state.get("completed_steps", []), "data_quality"],
    }


def outlier_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Outlier Node")
    agent = OutlierAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "outlier_report": out.data.get("outlier_reports", []),
        "should_pause": out.needs_approval,
        "pending_decision": out.approval_context,
        "current_step": "missing_values",
        "completed_steps": [*state.get("completed_steps", []), "outlier"],
    }


def missing_values_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Missing Values Node")
    agent = MissingValuesAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
    ))
    return {
        **state,
        "missing_value_report": out.data.get("missing_value_plan", []),
        "current_step": "encoding",
        "completed_steps": [*state.get("completed_steps", []), "missing_values"],
    }


def encoding_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Encoding Node")
    agent = EncodingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "encoding_plan": out.data.get("encoding_plan", []),
        "current_step": "scaling",
        "completed_steps": [*state.get("completed_steps", []), "encoding"],
    }


def scaling_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Scaling Node")
    agent = ScalingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "scaling_plan": out.data.get("scaling_plan", []),
        "current_step": "transformation",
        "completed_steps": [*state.get("completed_steps", []), "scaling"],
    }


def transformation_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Transformation Node")
    agent = TransformationAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "transformation_plan": out.data.get("transformation_plan", []),
        "current_step": "feature_engineering",
        "completed_steps": [*state.get("completed_steps", []), "transformation"],
    }


def feature_engineering_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Feature Engineering Node")
    agent = FeatureEngineeringAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "feature_engineering_plan": out.data.get("feature_engineering_plan", []),
        "current_step": "feature_selection",
        "completed_steps": [*state.get("completed_steps", []), "feature_engineering"],
    }


def feature_selection_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Feature Selection Node")
    agent = FeatureSelectionAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={
            "target_column": state.get("target_column"),
            "task_type": state.get("problem_type", "classification"),
        },
    ))
    return {
        **state,
        "feature_selection_result": out.data.get("feature_selection_results", []),
        "feature_columns": out.data.get("selected_features", []),
        "current_step": "leakage_detection",
        "completed_steps": [*state.get("completed_steps", []), "feature_selection"],
    }


def leakage_node(state: AgentState) -> AgentState:
    logger.info("[PreprocessingGraph] Running Leakage Detection Node")
    agent = LeakageDetectionAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    should_halt = out.data.get("should_halt_training", False)
    return {
        **state,
        "leakage_report": out.data,
        "should_pause": should_halt,
        "current_step": "HALTED" if should_halt else "COMPLETE_PREPROCESSING",
        "completed_steps": [*state.get("completed_steps", []), "leakage_detection"],
    }


# ─── Conditional Routing ───────────────────────────────────────────────────────

def check_leakage_condition(state: AgentState) -> Literal["continue", "halt"]:
    if state.get("should_pause") or state.get("leakage_report", {}).get("should_halt_training"):
        return "halt"
    return "continue"


# ─── Graph Builder ─────────────────────────────────────────────────────────────

def build_preprocessing_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("intake", intake_node)
    graph.add_node("profiling", profiling_node)
    graph.add_node("data_quality", data_quality_node)
    graph.add_node("outlier", outlier_node)
    graph.add_node("missing_values", missing_values_node)
    graph.add_node("encoding", encoding_node)
    graph.add_node("scaling", scaling_node)
    graph.add_node("transformation", transformation_node)
    graph.add_node("feature_engineering", feature_engineering_node)
    graph.add_node("feature_selection", feature_selection_node)
    graph.add_node("leakage", leakage_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "profiling")
    graph.add_edge("profiling", "data_quality")
    graph.add_edge("data_quality", "outlier")
    graph.add_edge("outlier", "missing_values")
    graph.add_edge("missing_values", "encoding")
    graph.add_edge("encoding", "scaling")
    graph.add_edge("scaling", "transformation")
    graph.add_edge("transformation", "feature_engineering")
    graph.add_edge("feature_engineering", "feature_selection")
    graph.add_edge("feature_selection", "leakage")

    graph.add_conditional_edges(
        "leakage",
        check_leakage_condition,
        {"continue": END, "halt": END},
    )

    return graph.compile()
