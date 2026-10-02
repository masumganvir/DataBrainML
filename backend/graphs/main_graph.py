"""
Agentic AutoML Intelligence Platform — Main Graph
Master LangGraph orchestrating ingestion, analysis, preprocessing, training, optimization, deployment, monitoring, and retraining.
"""

from graphs.master_graph import build_master_graph, execute_master_workflow

build_main_graph = build_master_graph
execute_main_workflow = execute_master_workflow

__all__ = [
    "build_main_graph",
    "execute_main_workflow",
]
