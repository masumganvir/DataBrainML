"""
DataWise AI — ModelRegistryAgent Tests
"""

import os
import tempfile
import pytest
import pandas as pd
from agents.model_registry_agent.agent import ModelRegistryAgent
from agents.base import AgentInput


@pytest.fixture
def sample_csv():
    df = pd.DataFrame({
        "feature_a": [1, 2, 3, 4, 5],
        "feature_b": [10.5, 20.1, 15.2, 30.0, 25.4],
        "category": ["A", "B", "A", "B", "C"],
        "target": [0, 1, 0, 1, 0],
    })
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_model_registry_agent_execution(sample_csv):
    agent = ModelRegistryAgent(session_id="test_model_registry_agent")
    out = agent.run(AgentInput(
        session_id="test_model_registry_agent",
        dataset_path=sample_csv,
        parameters={"target_column": "target"},
    ))
    assert out.status == 'success'
