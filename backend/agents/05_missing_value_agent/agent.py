"""
DataWise AI — Agent 05: Missing Value Agent Implementation
"""

from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.data_quality import detect_missing_values


class MissingValueDecisionAgent:
    """Agent 05: Formulates leakage-safe missing value strategies."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Missing Value Agent"

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

                missing_info = detect_missing_values(df)
                plan: Dict[str, str] = {}

                for col_info in missing_info.get("columns_with_missing", []):
                    col = col_info["column"]
                    dtype = col_info["dtype"]
                    pct = col_info["missing_pct"]

                    if "float" in dtype or "int" in dtype:
                        if pct < 5.0:
                            plan[col] = "median"
                        elif pct < 20.0:
                            plan[col] = "KNNImputer"
                        else:
                            plan[col] = "median_with_indicator"
                    else:
                        plan[col] = "most_frequent" if pct < 15.0 else "constant_unknown"

                count = missing_info["missing_columns_count"]
                summary = (
                    f"Missing Value Agent evaluated {len(df.columns)} columns. "
                    f"{count} columns have missing values. "
                    f"Tailored imputation plan generated for all {count} columns."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "missing_analysis": missing_info,
                        "imputation_plan": plan,
                        "missing_columns_count": count,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "detect_missing_values", "status": "ready"},
                summary="Missing Value Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Missing Value Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Missing Value Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
