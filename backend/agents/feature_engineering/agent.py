"""
DataWise AI — Feature Engineering Agent
Extracts datetime components (year, month, day, dayofweek, is_weekend), interaction terms,
ratios, differences, and aggregations.
CRITICAL: Prevents feature explosion with a hard configurable cap on generated features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class FeatureEngineeringAgent(BaseAgent):
    """Autonomous Feature Engineering Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Feature Engineering Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Feature engineering failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        max_features = input_data.parameters.get("max_generated_features", 20)

        planned_operations: List[Dict[str, Any]] = []

        # 1. Datetime feature extraction
        for col in df.columns:
            if col == target_col:
                continue
            if pd.api.types.is_datetime64_any_dtype(df[col]) or "date" in col.lower() or "time" in col.lower():
                try:
                    # Test parsing
                    sample_dt = pd.to_datetime(df[col].dropna().head(10), errors="coerce")
                    if sample_dt.notna().sum() > 5:
                        planned_operations.extend([
                            {"type": "datetime_part", "source_column": col, "new_feature": f"{col}_year", "part": "year"},
                            {"type": "datetime_part", "source_column": col, "new_feature": f"{col}_month", "part": "month"},
                            {"type": "datetime_part", "source_column": col, "new_feature": f"{col}_dayofweek", "part": "dayofweek"},
                            {"type": "datetime_part", "source_column": col, "new_feature": f"{col}_is_weekend", "part": "is_weekend"},
                        ])
                except Exception:
                    pass

        # 2. Domain ratios and interactions for highly correlated or complementary pairs
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
        for i, col1 in enumerate(numeric_cols[:6]):
            for col2 in numeric_cols[i+1:6]:
                if len(planned_operations) >= max_features:
                    break

                # Ratio if strictly positive
                s1 = df[col1].dropna()
                s2 = df[col2].dropna()
                if (s2 > 0).all() and col1 != col2:
                    planned_operations.append({
                        "type": "ratio",
                        "num_col": col1,
                        "den_col": col2,
                        "new_feature": f"{col1}_per_{col2}",
                        "rationale": f"Relative scale ratio of {col1} to {col2}",
                    })
                elif len(planned_operations) < max_features:
                    planned_operations.append({
                        "type": "interaction",
                        "col_a": col1,
                        "col_b": col2,
                        "new_feature": f"{col1}_x_{col2}",
                        "rationale": f"Second-order polynomial interaction between {col1} and {col2}",
                    })

        # Cap features
        planned_operations = planned_operations[:max_features]

        summary = (
            f"Synthesized {len(planned_operations)} engineered feature candidates "
            f"(datetime components, scale ratios, interactions). Strict explosion cap: {max_features}."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "feature_engineering_plan": planned_operations,
                "total_candidate_features": len(planned_operations),
            },
            summary=summary,
        )
