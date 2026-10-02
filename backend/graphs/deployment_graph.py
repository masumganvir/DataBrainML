"""
DataWise AI — Deployment Subgraph (LangGraph Section 5)
Orchestrates model artifact serialization, packaging, versioning in registry,
and production inference endpoint deployment.
"""

from __future__ import annotations

from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.artifact_generation import ArtifactGenerationAgent
from agents.deployment import DeploymentAgent


def artifact_generation_node(state: AgentState) -> AgentState:
    logger.info("[DeploymentGraph] Running Artifact Packaging Node")
    agent = ArtifactGenerationAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={
            "champion_model": state.get("best_model", "champion_model"),
            "problem_type": state.get("problem_type", "classification"),
        },
    ))
    return {
        **state,
        "model_version": out.data.get("model_version", "1.0.0"),
        "model_path": out.data.get("artifact_path", ""),
        "current_step": "deployment",
        "completed_steps": [*state.get("completed_steps", []), "artifact_generation"],
    }


def deployment_node(state: AgentState) -> AgentState:
    logger.info("[DeploymentGraph] Running Deployment Node")
    agent = DeploymentAgent(session_id=state.get("session_id", ""))
    out = agent.run(AgentInput(
        session_id=state.get("session_id", ""),
        parameters={
            "model_version": state.get("model_version", "1.0.0"),
            "champion_model": state.get("best_model", "champion_model"),
        },
    ))
    return {
        **state,
        "deployment_status": out.data.get("deployment_status", "staged"),
        "current_step": "deployment_complete",
        "completed_steps": [*state.get("completed_steps", []), "deployment"],
    }


def build_deployment_graph() -> StateGraph:
    """Constructs the compiled DeploymentGraph subgraph."""
    graph = StateGraph(AgentState)
    graph.add_node("artifact_generation", artifact_generation_node)
    graph.add_node("deployment", deployment_node)

    graph.set_entry_point("artifact_generation")
    graph.add_edge("artifact_generation", "deployment")
    graph.add_edge("deployment", END)

    return graph.compile()
