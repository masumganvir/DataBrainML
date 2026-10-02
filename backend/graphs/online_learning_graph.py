"""
Agentic AutoML Intelligence Platform — Online Learning Graph
LangGraph StateGraph governing incremental updates, shadow evaluation, and buffering.
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END
import pandas as pd

from graphs.state import AgentState
from agents.base import AgentInput
from agents.online_learning_agent.agent import OnlineLearningAgent
from agents.retraining_decision_agent.agent import RetrainingDecisionAgent
from ml.online_learning import online_learning_engine, ContinuousLearningPolicy
from deployment.shadow_manager import deployment_manager


# ─── Node Functions ────────────────────────────────────────────────────────────

def validate_batch_node(state: AgentState) -> AgentState:
    logger.info("[OnlineLearningGraph] Validating incoming labeled batch")
    batch_data = state.get("new_batch_data", [])
    valid = len(batch_data) > 0
    return {
        **state,
        "batch_validated": valid,
        "batch_size": len(batch_data),
        "current_step": "capability_check",
        "completed_steps": [*state.get("completed_steps", []), "validate_batch"],
    }


def capability_check_node(state: AgentState) -> AgentState:
    logger.info("[OnlineLearningGraph] Checking model incremental learning support")
    model = state.get("best_model") or (
        deployment_manager._version_registry.get(deployment_manager.active_version)
        if deployment_manager.active_version else None
    )
    supported = online_learning_engine.supports_incremental_learning(model) if model else False
    return {
        **state,
        "incremental_supported": supported,
        "current_step": "incremental_update" if supported else "accumulate_buffer",
        "completed_steps": [*state.get("completed_steps", []), "capability_check"],
    }


def route_online_capability(state: AgentState) -> str:
    if state.get("incremental_supported", False):
        return "incremental_update"
    return "accumulate_buffer"


def incremental_update_node(state: AgentState) -> AgentState:
    logger.info("[OnlineLearningGraph] Performing safe shadow partial_fit update")
    agent = OnlineLearningAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "model": state.get("best_model"),
            "X_new": state.get("new_X"),
            "y_new": state.get("new_y"),
            "val_X": state.get("val_X"),
            "val_y": state.get("val_y"),
            "policy": state.get("online_policy", "INCREMENTAL"),
        },
    ))
    promoted = out.data.get("promoted", False)
    return {
        **state,
        "online_update_result": out.data,
        "model_promoted": promoted,
        "current_step": "completed",
        "completed_steps": [*state.get("completed_steps", []), "incremental_update"],
    }


def accumulate_buffer_node(state: AgentState) -> AgentState:
    logger.info("[OnlineLearningGraph] Model does not support partial_fit; buffering data for batch retraining")
    current_buffer = state.get("accumulated_samples_count", 0) + state.get("batch_size", 0)
    return {
        **state,
        "accumulated_samples_count": current_buffer,
        "current_step": "retraining_decision",
        "completed_steps": [*state.get("completed_steps", []), "accumulate_buffer"],
    }


def retraining_eval_node(state: AgentState) -> AgentState:
    logger.info("[OnlineLearningGraph] Evaluating whether accumulated buffer triggers full retraining")
    agent = RetrainingDecisionAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "drift_report": state.get("drift_report", {}),
            "new_samples_count": state.get("accumulated_samples_count", 0),
            "model_supports_online": False,
        },
    ))
    return {
        **state,
        "retraining_decision": out.data,
        "should_pause": out.needs_approval,
        "current_step": "completed",
        "completed_steps": [*state.get("completed_steps", []), "retraining_decision"],
    }


# ─── Graph Construction ────────────────────────────────────────────────────────

def create_online_learning_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("validate_batch", validate_batch_node)
    workflow.add_node("capability_check", capability_check_node)
    workflow.add_node("incremental_update", incremental_update_node)
    workflow.add_node("accumulate_buffer", accumulate_buffer_node)
    workflow.add_node("retraining_eval", retraining_eval_node)

    workflow.set_entry_point("validate_batch")
    workflow.add_edge("validate_batch", "capability_check")

    workflow.add_conditional_edges(
        "capability_check",
        route_online_capability,
        {
            "incremental_update": "incremental_update",
            "accumulate_buffer": "accumulate_buffer",
        }
    )

    workflow.add_edge("accumulate_buffer", "retraining_eval")
    workflow.add_edge("incremental_update", END)
    workflow.add_edge("retraining_eval", END)

    return workflow.compile()


online_learning_subgraph = create_online_learning_graph()
