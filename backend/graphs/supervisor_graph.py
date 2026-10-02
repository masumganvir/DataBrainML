"""
DataWise AI — SupervisorGraph (Main LangGraph Orchestrator - Section 5)
Main root graph coordinating all 9 subgraphs:
  1. DataAnalysisGraph
  2. PreprocessingGraph
  3. FeatureEngineeringGraph
  4. ModelSelectionGraph
  5. TrainingGraph
  6. EvaluationGraph
  7. DeploymentGraph
  8. MonitoringGraph
  9. RetrainingGraph
Includes typed state, conditional edges, checkpoints, and human-in-the-loop interrupts.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from loguru import logger
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graphs.state import AgentState, create_initial_agent_state
from graphs.data_analysis_graph import build_data_analysis_graph
from graphs.preprocessing_graph import build_preprocessing_graph
from graphs.feature_engineering_graph import build_feature_engineering_graph
from graphs.model_selection_graph import build_model_selection_graph
from graphs.training_graph import build_training_graph
from graphs.evaluation_graph import build_evaluation_graph
from graphs.deployment_graph import build_deployment_graph
from graphs.monitoring_graph import build_monitoring_graph
from graphs.retraining_graph import build_retraining_graph
from agents.supervisor import SupervisorAgent
from agents.base import AgentInput


# ─── Master Supervisor Nodes ───────────────────────────────────────────────────

def supervisor_planning_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Supervisor Planning Node executing")
    supervisor = SupervisorAgent(session_id=state.get("session_id", ""))
    out = supervisor.run(AgentInput(
        session_id=state.get("session_id", ""),
        dataset_path=state.get("dataset_path"),
        parameters={
            "problem_type": state.get("problem_type", "classification"),
            "current_step": state.get("current_step", "intake"),
        },
    ))
    return {
        **state,
        "current_agent": "supervisor",
        "current_step": "DATA_ANALYSIS_PIPELINE",
        "completed_steps": [*state.get("completed_steps", []), "supervisor_plan"],
    }


def data_analysis_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking DataAnalysisGraph Subgraph")
    subgraph = build_data_analysis_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def preprocessing_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking PreprocessingGraph Subgraph")
    subgraph = build_preprocessing_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def feature_engineering_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking FeatureEngineeringGraph Subgraph")
    subgraph = build_feature_engineering_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def human_approval_gate_node(state: AgentState) -> AgentState:
    """Human-in-the-loop gate: pause execution if destructive actions or confirmation needed."""
    logger.info("[SupervisorGraph] Evaluating Human Approval Gate")
    if state.get("should_pause") and state.get("pending_decision"):
        logger.warning(f"[SupervisorGraph] Approval required: {state.get('pending_decision')}")
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


def model_selection_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking ModelSelectionGraph Subgraph")
    subgraph = build_model_selection_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def training_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking TrainingGraph Subgraph")
    subgraph = build_training_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def evaluation_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking EvaluationGraph Subgraph")
    subgraph = build_evaluation_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def deployment_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking DeploymentGraph Subgraph")
    subgraph = build_deployment_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


def monitoring_subgraph_node(state: AgentState) -> AgentState:
    logger.info("[SupervisorGraph] Invoking MonitoringGraph Subgraph")
    subgraph = build_monitoring_graph()
    result = subgraph.invoke(state)
    return {**state, **result}


# ─── Conditional Logic ─────────────────────────────────────────────────────────

def check_approval_gate(state: AgentState) -> Literal["proceed", "interrupt"]:
    if state.get("should_pause") and state.get("pending_decision"):
        return "interrupt"
    return "proceed"


def check_leakage_safety(state: AgentState) -> Literal["safe", "halt"]:
    if state.get("leakage_report", {}).get("should_halt_training"):
        logger.error("[SupervisorGraph] HALTING: Severe data leakage detected. Aborting training.")
        return "halt"
    return "safe"


# ─── Supervisor Graph Construction ─────────────────────────────────────────────

def build_supervisor_graph(checkpointer: Optional[Any] = None) -> StateGraph:
    """Builds and compiles the complete SupervisorGraph with 9 subgraphs & approval interrupts."""
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_planning_node)
    graph.add_node("data_analysis", data_analysis_subgraph_node)
    graph.add_node("preprocessing", preprocessing_subgraph_node)
    graph.add_node("feature_engineering", feature_engineering_subgraph_node)
    graph.add_node("approval_gate", human_approval_gate_node)
    graph.add_node("model_selection", model_selection_subgraph_node)
    graph.add_node("training", training_subgraph_node)
    graph.add_node("evaluation", evaluation_subgraph_node)
    graph.add_node("deployment", deployment_subgraph_node)
    graph.add_node("monitoring", monitoring_subgraph_node)

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "data_analysis")
    graph.add_edge("data_analysis", "preprocessing")
    graph.add_edge("preprocessing", "feature_engineering")

    # Leakage check before approval gate
    graph.add_conditional_edges(
        "feature_engineering",
        check_leakage_safety,
        {"safe": "approval_gate", "halt": END},
    )

    # Human-in-the-loop interrupt
    graph.add_conditional_edges(
        "approval_gate",
        check_approval_gate,
        {"proceed": "model_selection", "interrupt": END},
    )

    graph.add_edge("model_selection", "training")
    graph.add_edge("training", "evaluation")
    graph.add_edge("evaluation", "deployment")
    graph.add_edge("deployment", "monitoring")
    graph.add_edge("monitoring", END)

    cp = checkpointer or MemorySaver()
    return graph.compile(checkpointer=cp)


SupervisorGraph = build_supervisor_graph
