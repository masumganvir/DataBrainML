"""
DataWise AI — Underfitting Detection Agent Tests
"""

import pytest
from agents.underfitting_detection_agent.agent import UnderfittingDetectionAgent
from agents.base import AgentInput


def test_underfitting_detected():
    agent = UnderfittingDetectionAgent(session_id="test_underfit_session")
    # Both train and test are poor (0.42 and 0.40)
    out = agent.run(AgentInput(
        session_id="test_underfit_session",
        parameters={
            "train_score": 0.42,
            "val_score": 0.40,
            "model_name": "SimpleLinearModel",
        },
    ))
    assert out.status == "warning"
    report = out.data["underfitting_report"]
    assert report["is_underfitting"] is True
    assert report["severity"] == "severe"
    assert len(report["recommended_actions"]) > 0


def test_no_underfitting_well_fitted():
    agent = UnderfittingDetectionAgent(session_id="test_fit_session")
    # Good performance (0.88 train, 0.85 val)
    out = agent.run(AgentInput(
        session_id="test_fit_session",
        parameters={
            "train_score": 0.88,
            "val_score": 0.85,
            "model_name": "HistGradientBoosting",
        },
    ))
    assert out.status == "success"
    report = out.data["underfitting_report"]
    assert report["is_underfitting"] is False
    assert report["severity"] == "none"
