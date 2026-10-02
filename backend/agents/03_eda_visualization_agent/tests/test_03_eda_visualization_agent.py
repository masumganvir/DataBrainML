"""
Unit tests for EDA & Visualization Agent
"""

import importlib
import pytest

mod = importlib.import_module("agents.03_eda_visualization_agent.agent")
schemas_mod = importlib.import_module("agents.03_eda_visualization_agent.schemas")


def test_03_eda_visualization_agent_execution():
    agent_classes = [v for k, v in mod.__dict__.items() if k.endswith("Agent") and k not in ("AgentInput", "AgentOutput") and isinstance(v, type)]
    assert len(agent_classes) >= 1
    AgentClass = agent_classes[0]
    agent = AgentClass(session_id="test_session")
    inp = schemas_mod.AgentInput(session_id="test_session")
    res = agent.analyze(inp)
    assert res.status == "success"
    assert "EDA & Visualization Agent" in res.agent_name
