"""
Unit tests for Data Quality Agent
"""

import importlib
import pytest

mod = importlib.import_module("agents.02_data_quality_agent.agent")
schemas_mod = importlib.import_module("agents.02_data_quality_agent.schemas")


def test_02_data_quality_agent_execution():
    agent_classes = [v for k, v in mod.__dict__.items() if k.endswith("Agent") and k not in ("AgentInput", "AgentOutput") and isinstance(v, type)]
    assert len(agent_classes) >= 1
    AgentClass = agent_classes[0]
    agent = AgentClass(session_id="test_session")
    inp = schemas_mod.AgentInput(session_id="test_session")
    res = agent.analyze(inp)
    assert res.status == "success"
    assert "Data Quality Agent" in res.agent_name
