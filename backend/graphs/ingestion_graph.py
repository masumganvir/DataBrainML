"""
Agentic AutoML Intelligence Platform — Ingestion Graph
Unified LangGraph StateGraph supporting Mode A (Files) and Mode B (Database & Real-Time Streams).
"""

from __future__ import annotations

from typing import Any, Dict, Literal
from loguru import logger
from langgraph.graph import StateGraph, END

from graphs.state import AgentState
from agents.base import AgentInput
from agents.dataset_ingestion_agent.agent import DatasetIngestionAgent
from agents.database_connector_agent.agent import DatabaseConnectorAgent
from agents.database_security_agent.agent import DatabaseSecurityAgent
from agents.schema_discovery_agent.agent import SchemaDiscoveryAgent
from agents.dataset_profiling_agent.agent import DatasetProfilingAgent
from connectors.registry import ConnectorRegistry


# ─── Node Functions ────────────────────────────────────────────────────────────

def route_ingestion_source(state: AgentState) -> str:
    source_type = state.get("source_type", "file").lower()
    if source_type in ("file", "csv", "excel", "parquet", "json"):
        return "file_ingestion"
    return "database_connection"


def file_ingestion_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Running File Ingestion (Mode A)")
    agent = DatasetIngestionAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state.get("dataset_path"),
        parameters={"dataset_path": state.get("dataset_path")},
    ))
    return {
        **state,
        "dataset_metadata": out.data,
        "current_step": "profiling",
        "completed_steps": [*state.get("completed_steps", []), "file_ingestion"],
    }


def database_connection_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Running Database Connection (Mode B)")
    agent = DatabaseConnectorAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "source_type": state.get("source_type", "postgresql"),
            "connection_uri": state.get("connection_uri", ""),
        },
    ))
    return {
        **state,
        "connection_test": out.data,
        "current_step": "security_validation",
        "completed_steps": [*state.get("completed_steps", []), "database_connection"],
    }


def security_validation_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Validating database security & read-only constraints")
    agent = DatabaseSecurityAgent(session_id=state["session_id"])
    sample_query = state.get("sample_query") or f"SELECT 1;"
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={"sql_query": sample_query},
    ))
    is_safe = out.data.get("is_safe", True)
    return {
        **state,
        "security_validation": out.data,
        "should_pause": not is_safe,
        "current_step": "schema_discovery" if is_safe else "blocked",
        "completed_steps": [*state.get("completed_steps", []), "security_validation"],
    }


def schema_discovery_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Running Schema Discovery")
    agent = SchemaDiscoveryAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        parameters={
            "source_type": state.get("source_type", "postgresql"),
            "connection_uri": state.get("connection_uri", ""),
        },
    ))
    profile = out.data
    return {
        **state,
        "schema_profile": profile,
        "target_column": profile.get("candidate_targets", [None])[0] if profile.get("candidate_targets") else state.get("target_column"),
        "current_step": "sample_table",
        "completed_steps": [*state.get("completed_steps", []), "schema_discovery"],
    }


def sample_table_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Sampling table for data profiling")
    source_type = state.get("source_type", "sqlite")
    conn_uri = state.get("connection_uri", "")
    target_table = state.get("target_table")

    if not target_table and state.get("schema_profile", {}).get("tables"):
        target_table = state["schema_profile"]["tables"][0]["table_name"]

    try:
        connector = ConnectorRegistry.get_connector(source_type=source_type, connection_uri=conn_uri)
        df = connector.sample_table(table_name=target_table or "data", limit=2000)
        sample_path = f"./data/uploads/{state['session_id']}_db_sample.csv"
        df.to_csv(sample_path, index=False)
        return {
            **state,
            "dataset_path": sample_path,
            "current_step": "profiling",
            "completed_steps": [*state.get("completed_steps", []), "sample_table"],
        }
    except Exception as e:
        logger.error(f"[IngestionGraph] Sample table failed: {e}")
        return {
            **state,
            "error": str(e),
            "current_step": "error",
        }


def profiling_node(state: AgentState) -> AgentState:
    logger.info("[IngestionGraph] Running Dataset Profiling")
    agent = DatasetProfilingAgent(session_id=state["session_id"])
    out = agent.run(AgentInput(
        session_id=state["session_id"],
        dataset_path=state.get("dataset_path"),
        parameters={"dataset_path": state.get("dataset_path")},
    ))
    return {
        **state,
        "profiling_report": out.data,
        "current_step": "completed",
        "completed_steps": [*state.get("completed_steps", []), "profiling"],
    }


# ─── Graph Construction ────────────────────────────────────────────────────────

def create_ingestion_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("file_ingestion", file_ingestion_node)
    workflow.add_node("database_connection", database_connection_node)
    workflow.add_node("security_validation", security_validation_node)
    workflow.add_node("schema_discovery", schema_discovery_node)
    workflow.add_node("sample_table", sample_table_node)
    workflow.add_node("profiling", profiling_node)

    # Entry conditional router
    workflow.set_conditional_entry_point(
        route_ingestion_source,
        {
            "file_ingestion": "file_ingestion",
            "database_connection": "database_connection",
        }
    )

    # Mode A edge
    workflow.add_edge("file_ingestion", "profiling")

    # Mode B pipeline
    workflow.add_edge("database_connection", "security_validation")
    workflow.add_edge("security_validation", "schema_discovery")
    workflow.add_edge("schema_discovery", "sample_table")
    workflow.add_edge("sample_table", "profiling")

    workflow.add_edge("profiling", END)

    return workflow.compile()


ingestion_subgraph = create_ingestion_graph()
build_ingestion_graph = create_ingestion_graph

