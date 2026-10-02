"""
DataWise AI — Main Master LangGraph
"""

from __future__ import annotations
from graphs.master_graph import build_master_graph

def get_main_graph():
    return build_master_graph()

__all__ = ["get_main_graph", "build_master_graph"]
