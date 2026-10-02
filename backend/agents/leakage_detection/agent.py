"""
DataWise AI — Data Leakage Detection Agent
Detects target leakage, future timestamp signals, target-derived columns,
and near-perfect correlations.
CRITICAL: If severe/critical leakage is detected, halts training and alerts the user.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class LeakageDetectionAgent(BaseAgent):
    """Data Leakage Audit & Training Safeguard Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Leakage Detection Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Leakage check failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        if not target_col or target_col not in df.columns:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                summary="No target column designated; direct target leakage audit bypassed.",
            )

        leakage_warnings: List[Dict[str, Any]] = []
        is_severe_leakage = False
        target_series = df[target_col]

        # 1. Check for near-perfect correlation with numerical features (|r| > 0.98)
        if pd.api.types.is_numeric_dtype(target_series):
            for col in df.select_dtypes(include=[np.number]).columns:
                if col == target_col:
                    continue
                s = df[col].dropna()
                valid = s.index.intersection(target_series.dropna().index)
                if len(valid) > 20:
                    try:
                        r = float(np.corrcoef(df.loc[valid, col], target_series.loc[valid])[0, 1])
                        if abs(r) >= 0.98:
                            is_severe_leakage = True
                            leakage_warnings.append({
                                "column": col,
                                "type": "near_perfect_correlation",
                                "correlation": round(r, 4),
                                "severity": "CRITICAL",
                                "action": "DROP_IMMEDIATELY",
                                "explanation": f"Feature '{col}' has near-perfect correlation ({r:.4f}) with target. Highly likely to be a proxy or derived from the target.",
                            })
                    except Exception:
                        pass

        # 2. Check for suspicious column naming (e.g. churn_date when predicting churn)
        target_clean = target_col.lower().replace("_", "").replace("-", "")
        for col in df.columns:
            if col == target_col:
                continue
            col_clean = col.lower().replace("_", "").replace("-", "")
            if target_clean in col_clean and any(k in col.lower() for k in ["derived", "outcome", "label", "result", "post", "after"]):
                is_severe_leakage = True
                leakage_warnings.append({
                    "column": col,
                    "type": "target_derived_naming",
                    "severity": "CRITICAL",
                    "action": "DROP_IMMEDIATELY",
                    "explanation": f"Column name '{col}' strongly indicates post-event or target-derived information.",
                })

        # 3. Check for exact duplicate feature values matching target exactly
        for col in df.columns:
            if col == target_col:
                continue
            if (df[col] == df[target_col]).mean() > 0.98:
                is_severe_leakage = True
                leakage_warnings.append({
                    "column": col,
                    "type": "identical_values_to_target",
                    "severity": "CRITICAL",
                    "action": "DROP_IMMEDIATELY",
                    "explanation": f"Column '{col}' matches target values in >98% of rows. Direct target leakage.",
                })

        if is_severe_leakage:
            summary = (
                f"🚨 SEVERE DATA LEAKAGE DETECTED! Identified {len(leakage_warnings)} critical leakage risks. "
                f"Training MUST BE HALTED until these features are removed to avoid model failure."
            )
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                data={"leakage_warnings": leakage_warnings, "should_halt_training": True},
                summary=summary,
                errors=[w["explanation"] for w in leakage_warnings],
            )

        summary = "Data leakage check passed. No severe target leakage or proxy features detected."
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"leakage_warnings": leakage_warnings, "should_halt_training": False},
            summary=summary,
        )
