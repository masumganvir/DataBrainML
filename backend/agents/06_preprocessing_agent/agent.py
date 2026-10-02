"""
DataWise AI — Agent 06: Preprocessing Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.preprocessing import build_column_transformer


class PreprocessingPipelineAgent:
    """Agent 06: Constructs reproducible sklearn ColumnTransformer pipelines."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Preprocessing Agent"

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
                features_df = df.drop(columns=[target]) if target and target in df.columns else df

                numeric_cols = list(features_df.select_dtypes(include=[np.number]).columns)
                categorical_cols = list(features_df.select_dtypes(exclude=[np.number]).columns)

                # Determine scaler
                scaler = input_data.parameters.get("scaler", "standard")
                encoder = input_data.parameters.get("encoder", "onehot")

                # Test building column transformer
                transformer = build_column_transformer(
                    numeric_features=numeric_cols,
                    categorical_features=categorical_cols,
                    scaler_method=scaler,
                    encoder_method=encoder,
                )

                summary = (
                    f"ColumnTransformer assembled: {len(numeric_cols)} numeric features ({scaler} scaler), "
                    f"{len(categorical_cols)} categorical features ({encoder} encoder)."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "numeric_features": numeric_cols,
                        "categorical_features": categorical_cols,
                        "scaler_selected": scaler,
                        "encoder_selected": encoder,
                        "pipeline_constructed": True,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "build_column_transformer", "status": "ready"},
                summary="Preprocessing Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Preprocessing Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Preprocessing Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
