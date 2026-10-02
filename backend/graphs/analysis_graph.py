"""
Agentic AutoML Intelligence Platform — Analysis Subgraph
Canonical export for exploratory data analysis, profiling, and quality graph.
"""

from graphs.data_analysis_graph import build_data_analysis_graph

create_analysis_graph = build_data_analysis_graph
build_analysis_graph = build_data_analysis_graph

__all__ = [
    "create_analysis_graph",
    "build_analysis_graph",
]
