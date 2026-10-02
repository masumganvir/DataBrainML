"""
DataWise AI — Master Graph & Supervisor Orchestrator
Coordinates subgraphs (preprocessing, training, monitoring), manages checkpointing,
conditional branching, human-in-the-loop interrupts, retry limits, and loop bounds.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Literal, Optional
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graphs.state import AgentState, create_initial_agent_state
from graphs.preprocessing_graph import build_preprocessing_graph
from graphs.training_graph import build_training_graph
from graphs.optimization_graph import build_optimization_graph
from graphs.monitoring_graph import build_monitoring_graph
from agents.supervisor import SupervisorAgent
from agents.visualization import VisualizationAgent
from agents.base import AgentInput


# ─── Master Supervisor Nodes ───────────────────────────────────────────────────

def supervisor_planning_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Supervisor Planning Node executing")
    supervisor = SupervisorAgent(session_id=state["session_id"])
    out = supervisor.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state.get("dataset_path"),
        parameters={
            "problem_type": state.get("problem_type", "classification"),
            "current_step": state.get("current_step", "intake"),
        },
    ))
    return {
        **state,
        "current_agent": "supervisor",
        "current_step": "PREPROCESSING_PIPELINE",
        "completed_steps": [*state.get("completed_steps", []), "supervisor_plan"],
    }


def preprocessing_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Executing Preprocessing Subgraph")
    subgraph = build_preprocessing_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def human_approval_gate_node(state: AgentState) -> AgentState:
    """Pause execution if destructive outlier treatment or target confirmation is required."""
    logger.info("[MasterGraph] Evaluating Human Approval Gate")
    if state.get("should_pause") and state.get("pending_decision"):
        logger.warning(f"[MasterGraph] Human approval required for: {state.get('pending_decision')}")
        return {
            **state,
            "current_step": "AWAITING_APPROVAL",
        }
    return {
        **state,
        "should_pause": False,
        "current_step": "TRAINING_PIPELINE",
        "completed_steps": [*state.get("completed_steps", []), "human_approval_gate"],
    }


def training_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Executing Training & AutoML Subgraph")
    subgraph = build_training_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def optimization_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Executing Autonomous Optimization Flowchart Subgraph")
    subgraph = build_optimization_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def master_visualization_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Generating Master Visualizations")
    agent = VisualizationAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state["dataset_path"],
        parameters={"target_column": state.get("target_column")},
    ))
    return {
        **state,
        "visualization_results": out.data.get("visualizations", []),
        "current_step": "MONITORING_SETUP",
        "completed_steps": [*state.get("completed_steps", []), "visualization"],
    }


def monitoring_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[MasterGraph] Executing Monitoring Baseline Setup")
    subgraph = build_monitoring_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


# ─── Conditional Edge Logic ────────────────────────────────────────────────────

def check_approval_gate(state: AgentState) -> Literal["proceed", "interrupt"]:
    if state.get("should_pause") and state.get("pending_decision"):
        return "interrupt"
    return "proceed"


def check_leakage_safety(state: AgentState) -> Literal["safe", "halt"]:
    if state.get("leakage_report", {}).get("should_halt_training"):
        logger.error("[MasterGraph] HALTING: Severe data leakage detected. Aborting training.")
        return "halt"
    return "safe"


# ─── Master Graph Construction ─────────────────────────────────────────────────

def build_master_graph(checkpointer: Optional[Any] = None) -> StateGraph:
    """Builds and compiles the full Master LangGraph with subgraphs and interrupts."""
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_planning_node)
    graph.add_node("preprocessing", preprocessing_subgraph_node)
    graph.add_node("approval_gate", human_approval_gate_node)
    graph.add_node("training", training_subgraph_node)
    graph.add_node("optimization", optimization_subgraph_node)
    graph.add_node("visualization", master_visualization_node)
    graph.add_node("monitoring", monitoring_subgraph_node)

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "preprocessing")

    # Check for severe leakage before proceeding to approval / training
    graph.add_conditional_edges(
        "preprocessing",
        check_leakage_safety,
        {"safe": "approval_gate", "halt": END},
    )

    # Human-in-the-loop gate
    graph.add_conditional_edges(
        "approval_gate",
        check_approval_gate,
        {"proceed": "training", "interrupt": END},
    )

    graph.add_edge("training", "optimization")
    graph.add_edge("optimization", "visualization")
    graph.add_edge("visualization", "monitoring")
    graph.add_edge("monitoring", END)

    cp = checkpointer or MemorySaver()
    return graph.compile(checkpointer=cp)


# Asynchronous workflow execution helper
async def execute_master_workflow(
    dataset_path: str,
    session_id: str,
    target_column: Optional[str] = None,
    problem_type: str = "classification",
) -> AgentState:
    """Runs the master graph end-to-end on an ingested dataset."""
    initial_state = create_initial_agent_state(
        dataset_path=dataset_path,
        session_id=session_id,
        target_column=target_column,
        problem_type=problem_type,
    )
    master = build_master_graph()
    config = {"configurable": {"thread_id": session_id}}
    final_state = master.invoke(initial_state, config=config)
    return final_state
