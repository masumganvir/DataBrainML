"""
DataWise AI — Agent 07: Feature Engineering Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.feature_engineering import recommend_and_engineer_features


class FeatureAgent:
    """Agent 07: Formulates domain-informed, leakage-safe features with explicit rationale."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Feature Engineering Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                path = input_data.dataset_path
                ext = Path(path).suffix.lower()
                if ext in (".xlsx", ".xls"):
                    df = pd.read_excel(path)
                elif ext == ".json":
                    df = pd.read_json(path)
                else:
                    df = pd.read_csv(path, low_memory=False)

                target = input_data.parameters.get("target_column")
                fe_res = recommend_and_engineer_features(df, target_column=target)
                count = fe_res["recommendation_count"]

                summary = (
                    f"Feature Engineering Agent evaluated {len(df.columns)} columns. "
                    f"Recommended {count} justified candidate features "
                    "(ratios, interactions, and temporal decompositions)."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data=fe_res,
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "recommend_and_engineer_features", "status": "ready"},
                summary="Feature Engineering Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Feature Engineering Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Feature Engineering Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
