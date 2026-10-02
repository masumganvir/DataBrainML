"""
DataWise AI — Model Selection Subgraph (LangGraph Section 5)
Orchestrates problem type detection and candidate algorithm generation.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.problem_type import ProblemTypeAgent
from agents.model_selection import ModelSelectionAgent


def problem_type_node(state: AgentState) -> AgentState:
    logger.info("[ModelSelectionGraph] Running Problem Type Detection Node")
    agent = ProblemTypeAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
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
    logger.info("[ModelSelectionGraph] Running Model Selection Node")
    agent = ModelSelectionAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={"problem_type": state.get("problem_type", "classification")},
    ))
    return {
        **state,
        "candidate_models": out.data.get("candidate_models", []),
        "current_step": "model_selection_complete",
        "completed_steps": [*state.get("completed_steps", []), "model_selection"],
    }


def build_model_selection_graph() -> StateGraph:
    """Constructs the compiled ModelSelectionGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("problem_type", problem_type_node)
    graph.add_node("model_selection", model_selection_node)

    graph.set_entry_point("problem_type")
    graph.add_edge("problem_type", "model_selection")
    graph.add_edge("model_selection", END)

    return graph.compile()
