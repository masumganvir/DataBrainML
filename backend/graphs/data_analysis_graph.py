"""
DataWise AI — Data Analysis Subgraph (LangGraph Section 5)
Orchestrates dataset intake, profiling, quality audit, outlier intelligence,
missing value analysis, and target detection.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.intake import IntakeAgent
from agents.profiling import ProfilingAgent
from agents.data_quality import DataQualityAgent
from agents.outlier import OutlierAgent
from agents.missing_values import MissingValuesAgent


def intake_node(state: AgentState) -> AgentState:
    logger.info("[DataAnalysisGraph] Running Intake Node")
    agent = IntakeAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
    ))
    meta = out.data.get("metadata", {})
    return {
        **state,
        "dataset_metadata": meta,
        "current_step": "profiling",
        "completed_steps": [*state.get("completed_steps", []), "intake"],
    }


def profiling_node(state: AgentState) -> AgentState:
    logger.info("[DataAnalysisGraph] Running Profiling Node")
    agent = ProfilingAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
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
    logger.info("[DataAnalysisGraph] Running Data Quality Node")
    agent = DataQualityAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
    ))
    return {
        **state,
        "data_quality_report": out.data.get("quality_report", {}),
        "current_step": "outlier",
        "completed_steps": [*state.get("completed_steps", []), "data_quality"],
    }


def outlier_node(state: AgentState) -> AgentState:
    logger.info("[DataAnalysisGraph] Running Outlier Intelligence Node")
    agent = OutlierAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
    ))
    decisions = out.data.get("outlier_decisions", [])
    has_approval = any(d.get("requires_approval") for d in decisions)
    return {
        **state,
        "outlier_report": decisions,
        "should_pause": has_approval or state.get("should_pause", False),
        "pending_decision": decisions[0] if has_approval else state.get("pending_decision"),
        "current_step": "missing_values",
        "completed_steps": [*state.get("completed_steps", []), "outlier"],
    }


def missing_values_node(state: AgentState) -> AgentState:
    logger.info("[DataAnalysisGraph] Running Missing Values Analysis Node")
    agent = MissingValuesAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
    ))
    plans = out.data.get("imputation_plans", [])
    has_approval = any(p.get("requires_approval") for p in plans)
    return {
        **state,
        "missing_value_report": plans,
        "should_pause": has_approval or state.get("should_pause", False),
        "pending_decision": plans[0] if has_approval else state.get("pending_decision"),
        "current_step": "data_analysis_complete",
        "completed_steps": [*state.get("completed_steps", []), "missing_values"],
    }


def build_data_analysis_graph() -> StateGraph:
    """Constructs the compiled DataAnalysisGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("intake", intake_node)
    graph.add_node("profiling", profiling_node)
    graph.add_node("data_quality", data_quality_node)
    graph.add_node("outlier", outlier_node)
    graph.add_node("missing_values", missing_values_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "profiling")
    graph.add_edge("profiling", "data_quality")
    graph.add_edge("data_quality", "outlier")
    graph.add_edge("outlier", "missing_values")
    graph.add_edge("missing_values", END)

    return graph.compile()
