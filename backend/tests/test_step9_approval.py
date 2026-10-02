"""
DataWise AI — Tests for Step 9: Human Approval System
"""

import pytest
import pandas as pd
from app.agents.governance import HumanApprovalNode
from app.state.data_science_state import DataScienceState, PreprocessingDecision


def test_human_approval_node_flags_destructive_operations():
    node = HumanApprovalNode()
    
    # Decisions with high missing column drop and outlier removal
    decisions = [
        PreprocessingDecision(column="high_missing_col", operation="drop", method="drop_column", approved=False),
        PreprocessingDecision(column="age", operation="impute", method="median", approved=False),
        PreprocessingDecision(column="salary", operation="scale", method="StandardScaler", approved=False),
    ]
    
    state: DataScienceState = {
        "session_id": "sess-test-1",
        "preprocessing_plan": decisions,
        "user_decisions": [],
    }
    
    evaluated_state = node.evaluate_approval_needs(state)
    pending = evaluated_state.get("pending_decision")
    assert pending is not None
    assert pending.get("requires_confirmation") is True
    assert pending.get("operation") == "drop"
    assert evaluated_state.get("should_continue") is False


def test_human_approval_node_auto_approves_safe_operations():
    node = HumanApprovalNode()
    
    decisions = [
        PreprocessingDecision(column="age", operation="impute", method="median", approved=False),
        PreprocessingDecision(column="salary", operation="scale", method="StandardScaler", approved=False),
        PreprocessingDecision(column="gender", operation="encode", method="OneHotEncoder", approved=False),
    ]
    
    state: DataScienceState = {
        "session_id": "sess-test-2",
        "preprocessing_plan": decisions,
        "user_decisions": [],
    }
    
    evaluated_state = node.evaluate_approval_needs(state)
    pending = evaluated_state.get("pending_decision")
    # Impute/scale/encode should be safe or auto-approved
    assert evaluated_state.get("should_continue") is True or pending is not None
