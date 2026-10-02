"""
DataWise AI — Outlier Intelligence & Fraud Signal Preservation Test
Verifies that statistical outliers that correlate with meaningful rare events (e.g. Fraud)
are NEVER automatically dropped.
"""

from pathlib import Path
import pytest
import pandas as pd
from agents.outlier import OutlierAgent
from agents.base import AgentInput


def test_outlier_agent_preserves_fraud_signals():
    """Verify that OutlierAgent keeps rare predictive signals in fraud datasets."""
    dataset_path = Path("..") / "data" / "test_datasets" / "fraud_detection.csv"
    if not dataset_path.exists():
        dataset_path = Path("data") / "test_datasets" / "fraud_detection.csv"

    assert dataset_path.exists(), f"Fraud dataset not found at {dataset_path.resolve()}"

    agent = OutlierAgent(session_id="fraud_test_session")
    out = agent.run(AgentInput(
        session_id="fraud_test_session",
        dataset_path=str(dataset_path),
        parameters={"target_column": "is_fraud"},
    ))

    assert out.status in ("success", "needs_approval")
    reports = out.data.get("outlier_reports", [])
    assert len(reports) > 0, "Expected outliers to be detected in fraud dataset"

    # Find report for transaction_amount or risk_score
    fraud_correlated_reports = [
        r for r in reports if r.get("column") in ("transaction_amount", "risk_score")
    ]
    assert len(fraud_correlated_reports) > 0, "transaction_amount or risk_score should be flagged"

    for r in fraud_correlated_reports:
        # Crucial specification test: NEVER REMOVE predictive rare events
        assert r["recommended_action"] != "REMOVE", f"Column {r['column']} was erroneously marked for removal!"
        assert r["target_signal_detected"] is True, f"Target signal was not recognized for {r['column']}"
        assert r["recommended_action"] == "KEEP", f"Expected KEEP action for predictive outlier {r['column']}"
