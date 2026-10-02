"""
Unit tests for Agent 00: Orchestrator Agent
"""

import pytest
import importlib
orchestrator_mod = importlib.import_module("agents.00_orchestrator_agent.agent")
OrchestratorAgent = orchestrator_mod.OrchestratorAgent


def test_orchestrator_initial_transition():
    orchestrator = OrchestratorAgent(session_id="test_session_001", execution_mode="guided")
    transition = orchestrator.analyze()
    assert transition.to_stage == "PROFILING"


def test_orchestrator_guided_approval_gates():
    orchestrator = OrchestratorAgent(session_id="test_session_002", execution_mode="guided")
    orchestrator.record_stage_completed("MISSING_VALUES")
    transition = orchestrator.analyze("MISSING_VALUES")
    assert transition.to_stage == "PREPROCESSING"
    assert transition.requires_user_approval is True
    assert "Approve preprocessing plan" in transition.action_required


def test_orchestrator_autonomous_mode_skips_approval():
    orchestrator = OrchestratorAgent(session_id="test_session_003", execution_mode="autonomous")
    transition = orchestrator.analyze("MISSING_VALUES")
    assert transition.to_stage == "PREPROCESSING"
    assert transition.requires_user_approval is False
