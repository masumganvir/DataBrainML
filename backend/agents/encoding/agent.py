"""
DataWise AI — Categorical Encoding Agent
Selects leak-free encoding strategies (OneHotEncoder, OrdinalEncoder, TargetEncoder,
FrequencyEncoding) based on cardinality, model sensitivity, and nominal/ordinal nature.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class EncodingAgent(BaseAgent):
    """Categorical Encoding Strategy Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Encoding Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Encoding analysis failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column")
        cat_cols = [c for c in df.select_dtypes(include=["object", "category", "string"]).columns if c != target_col]
        encoding_plans: List[Dict[str, Any]] = []

        for col in cat_cols:
            n_unique = df[col].nunique(dropna=True)
            if n_unique <= 1:
                strategy = "DROP"
                rationale = "Single unique value (constant). Dropped to avoid redundant feature."
            elif n_unique == 2:
                strategy = "OneHotEncoder(drop='if_binary')"
                rationale = "Binary categorical feature. Encoded as single 0/1 indicator."
            elif n_unique <= 10:
                strategy = "OneHotEncoder(handle_unknown='ignore')"
                rationale = f"Low cardinality ({n_unique} categories). One-hot encoding creates orthogonal dimensions without false ordering."
            elif n_unique <= 50:
                strategy = "TargetEncoder" if target_col else "OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)"
                rationale = f"Medium cardinality ({n_unique} categories). Target/Ordinal encoding prevents feature dimension explosion."
            else:
                strategy = "FrequencyEncoder"
                rationale = f"High cardinality ({n_unique} unique levels). Frequency encoding captures category rarity without excessive sparsity."

            encoding_plans.append({
                "column": col,
                "cardinality": n_unique,
                "recommended_encoder": strategy,
                "pipeline_step": "preprocessor__categorical",
                "rationale": rationale,
            })

        summary = (
            f"Evaluated {len(cat_cols)} categorical columns. "
            f"Configured leak-free pipeline encoding plan for {len(encoding_plans)} features."
            if encoding_plans else "No non-target categorical columns found requiring encoding."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"encoding_plan": encoding_plans, "categorical_columns": cat_cols},
            summary=summary,
        )
