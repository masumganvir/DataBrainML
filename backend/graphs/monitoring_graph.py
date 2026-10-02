"""
DataWise AI — Monitoring & Retraining Subgraph
Modular LangGraph StateGraph governing post-deployment feature drift detection,
prediction distribution analysis, automated challenger retraining, and approval gates.
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.monitoring import MonitoringAgent
from agents.retraining import RetrainingAgent
from agents.deployment import DeploymentAgent


# ─── Node Functions ────────────────────────────────────────────────────────────

def monitoring_node(state: AgentState) -> AgentState:
    logger.info("[MonitoringGraph] Running Monitoring Node (Drift Detection)")
    agent = MonitoringAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={"session_id": state["session_id"]},
    ))
    drift = out.data.get("drift_detected", False)
    return {
        **state,
        "drift_report": out.data,
        "monitoring_status": "drift_detected" if drift else "healthy",
        "current_step": "retraining" if drift else "monitoring_idle",
        "completed_steps": [*state.get("completed_steps", []), "monitoring"],
    }


def retraining_node(state: AgentState) -> AgentState:
    logger.info("[MonitoringGraph] Running Retraining Node (Challenger vs Champion)")
    agent = RetrainingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "production_score": 0.82,
            "challenger_score": 0.88,
            "trigger_reason": "Covariate drift detected in input features",
        },
    ))
    return {
        **state,
        "retraining_status": out.data,
        "should_pause": out.needs_approval,
        "pending_decision": out.approval_context,
        "current_step": "deployment_approval",
        "completed_steps": [*state.get("completed_steps", []), "retraining"],
    }


def redeployment_node(state: AgentState) -> AgentState:
    logger.info("[MonitoringGraph] Promoting Challenger to Production Deployment")
    agent = DeploymentAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "champion_model": state.get("best_model", "ChallengerModel"),
            "feature_names": state.get("feature_columns", []),
        },
    ))
    return {
        **state,
        "deployment_status": "promoted",
        "model_version": "v1.1.0",
        "current_step": "COMPLETE_RETRAINING",
        "completed_steps": [*state.get("completed_steps", []), "redeployment"],
    }


# ─── Conditional Edge ──────────────────────────────────────────────────────────

def check_drift_condition(state: AgentState) -> Literal["retrain", "idle"]:
    if state.get("drift_report", {}).get("drift_detected"):
        return "retrain"
    return "idle"


def check_approval_condition(state: AgentState) -> Literal["deploy", "pause"]:
    if state.get("should_pause"):
        return "pause"
    return "deploy"


# ─── Graph Builder ─────────────────────────────────────────────────────────────

def build_monitoring_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("monitoring", monitoring_node)
    graph.add_node("retraining", retraining_node)
    graph.add_node("redeployment", redeployment_node)

    graph.set_entry_point("monitoring")

    graph.add_conditional_edges(
        "monitoring",
        check_drift_condition,
        {"retrain": "retraining", "idle": END},
    )

    graph.add_conditional_edges(
        "retraining",
        check_approval_condition,
        {"deploy": "redeployment", "pause": END},
    )

    graph.add_edge("redeployment", END)

    return graph.compile()
