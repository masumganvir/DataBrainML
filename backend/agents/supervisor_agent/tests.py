"""
DataWise AI — Supervisor Agent Tests
"""

import pytest
from agents.supervisor_agent.agent import SupervisorAgent
from agents.base import AgentInput


def test_supervisor_workflow_planning():
    agent = SupervisorAgent(session_id="test_sup_session")
    out = agent.run(AgentInput(
        session_id="test_sup_session",
        parameters={"problem_type": "classification"},
    ))
    assert out.status == "success"
    plan = out.data.get("workflow_plan", {})
    assert plan["problem_type"] == "classification"
    assert "intake" in plan["execution_order"]
    assert "training" in plan["execution_order"]


def test_supervisor_retraining_workflow():
    agent = SupervisorAgent(session_id="test_sup_retrain")
    plan = agent.determine_workflow(needs_retraining=True)
    assert plan.execution_order == ["monitoring", "retraining", "model_comparison", "deployment"]
