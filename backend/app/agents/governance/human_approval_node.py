"""
DataWise AI — Human Approval & Interactive Decision Node
Enforces Human-in-the-Loop safeguards:
  - Halts automated workflow for destructive actions (e.g. dropping columns/rows)
  - Prepares structured decision requests with:
      * Context and rationale
      * Default recommended action
      * Selectable alternatives or custom overrides
  - Records user confirmations into immutable audit trail
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from loguru import logger

from app.state.data_science_state import DataScienceState


class HumanApprovalNode:
    """Evaluates state actions and pauses execution when human consensus is needed."""

    def evaluate_approval_needs(self, state: DataScienceState) -> Dict[str, Any]:
        """
        Evaluates state to determine if human intervention is required.
        Updates state with pending_decision and should_continue flags.
        """
        pending = self.inspect_proposed_actions(state)
        updated_state = dict(state)
        if pending:
            updated_state["pending_decision"] = pending
            updated_state["should_continue"] = False
        else:
            updated_state["pending_decision"] = None
            updated_state["should_continue"] = True
        return updated_state

    @staticmethod
    def inspect_proposed_actions(state: DataScienceState) -> Optional[Dict[str, Any]]:
        """
        Scans proposed preprocessing actions in the state.
        If a destructive or ambiguous action is found and has not yet been approved,
        returns a structured PendingDecision payload.
        """
        user_decisions = {}
        for d in state.get("user_decisions", []):
            if isinstance(d, dict):
                user_decisions[d.get("decision_key")] = d.get("decision_value")
            else:
                user_decisions[getattr(d, "decision_key", None)] = getattr(d, "decision_value", None)

        # 0. Check preprocessing plan directly for drop operations
        for plan_item in state.get("preprocessing_plan", []):
            op = plan_item.get("operation") if isinstance(plan_item, dict) else getattr(plan_item, "operation", None)
            approved = plan_item.get("approved") if isinstance(plan_item, dict) else getattr(plan_item, "approved", False)
            col = plan_item.get("column", "unknown") if isinstance(plan_item, dict) else getattr(plan_item, "column", "unknown")
            if op == "drop" and not approved:
                key = f"drop_column_{col}"
                if key not in user_decisions:
                    return {
                        "decision_id": key,
                        "stage": "PREPROCESSING_APPROVAL",
                        "category": "DESTRUCTIVE",
                        "operation": "drop",
                        "requires_confirmation": True,
                        "title": f"Approve Dropping Column: {col}",
                        "message": f"Proposal to drop column '{col}'. Destructive operations require confirmation.",
                        "recommended_choice": "approve_drop",
                        "options": [
                            {"value": "approve_drop", "label": f"Approve: Drop {col}"},
                            {"value": "keep", "label": f"Reject: Keep {col}"},
                        ],
                        "context": plan_item,
                    }

        # 1. Check for columns proposed to be dropped due to critical missingness
        missing_reports = state.get("missing_value_report", [])
        for r in missing_reports:
            if r.get("severity") == "CRITICAL" and r.get("recommended_strategy") == "drop_column":
                key = f"drop_column_{r['column']}"
                if key not in user_decisions:
                    return {
                        "decision_id": key,
                        "stage": "MISSING_VALUE_APPROVAL",
                        "category": "DESTRUCTIVE",
                        "title": f"Approve Dropping Column: {r['column']}",
                        "message": (
                            f"Column '{r['column']}' has {r['missing_pct']}% missing values. "
                            f"Imputing over half the data could introduce synthetic bias. "
                            f"Do you approve dropping this column from training features?"
                        ),
                        "recommended_choice": "approve_drop",
                        "options": [
                            {"value": "approve_drop", "label": "Approve: Drop Column (Recommended)"},
                            {"value": "keep_and_impute", "label": "Reject: Keep and Impute (Median/Mode)"},
                            {"value": "indicator_and_impute", "label": "Add Missing Indicator + Impute"},
                        ],
                        "context": r,
                    }

        # 2. Check for duplicate rows
        dup_report = state.get("duplicate_report", {})
        if dup_report.get("has_duplicates") and "drop_duplicates" not in user_decisions:
            cnt = dup_report.get("duplicate_count", 0)
            pct = dup_report.get("duplicate_pct", 0.0)
            return {
                "decision_id": "drop_duplicates",
                "stage": "DUPLICATE_REMOVAL_APPROVAL",
                "category": "DESTRUCTIVE",
                "title": "Approve Duplicate Row Removal",
                "message": (
                    f"Found {cnt} exact duplicate rows ({pct}% of dataset). "
                    f"Removing duplicates prevents train-test data leakage."
                ),
                "recommended_choice": "drop_duplicates",
                "options": [
                    {"value": "drop_duplicates", "label": f"Remove {cnt} Duplicate Rows (Recommended)"},
                    {"value": "keep_duplicates", "label": "Keep All Rows (No Changes)"},
                ],
                "context": dup_report,
            }

        return None
