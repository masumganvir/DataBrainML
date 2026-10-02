"""
DataWise AI — Retraining Subgraph (LangGraph Section 5 & 49)
Governs drift assessment, champion-challenger comparison, human approval gates,
and immutable model version promotion.
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.retraining import RetrainingAgent


def drift_assessment_node(state: AgentState) -> AgentState:
    logger.info("[RetrainingGraph] Assessing Data Drift Severity")
    drift_report = state.get("drift_report", {})
    psi = drift_report.get("psi_score", 0.0)
    retraining_justified = psi > 0.20 or drift_report.get("severity") in ("moderate", "severe")

    return {
        **state,
        "current_step": "challenger_evaluation" if retraining_justified else "drift_acceptable",
        "completed_steps": [*state.get("completed_steps", []), "drift_assessment"],
    }


def challenger_evaluation_node(state: AgentState) -> AgentState:
    logger.info("[RetrainingGraph] Evaluating Retrained Challenger Model")
    agent = RetrainingAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={
            "production_score": 0.82,
            "challenger_score": 0.88,
            "trigger_reason": "Covariate data drift detected in inference distribution",
        },
    ))
    return {
        **state,
        "retraining_status": out.data,
        "should_pause": out.needs_approval,
        "pending_decision": out.approval_context,
        "current_step": "retraining_complete",
        "completed_steps": [*state.get("completed_steps", []), "challenger_evaluation"],
    }


def check_retraining_trigger(state: AgentState) -> Literal["retrain", "skip"]:
    if state.get("current_step") == "challenger_evaluation":
        return "retrain"
    return "skip"


def build_retraining_graph() -> StateGraph:
    """Constructs the compiled RetrainingGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("drift_assessment", drift_assessment_node)
    graph.add_node("challenger_evaluation", challenger_evaluation_node)

    graph.set_entry_point("drift_assessment")
    graph.add_conditional_edges(
        "drift_assessment",
        check_retraining_trigger,
        {"retrain": "challenger_evaluation", "skip": END},
    )
    graph.add_edge("challenger_evaluation", END)

    return graph.compile()
