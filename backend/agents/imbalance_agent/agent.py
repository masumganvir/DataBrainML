"""
DataWise AI — ImbalanceAgent
Analyzes class distribution, calculates imbalance ratio, and recommends/applies
mitigation strategies (class weighting, SMOTE, focal loss, PR-AUC metric prioritization).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class ImbalanceAnalysisResult(BaseModel):
    is_imbalanced: bool = False
    imbalance_ratio: float = 1.0
    minority_class: Optional[Any] = None
    minority_percentage: float = 50.0
    class_counts: Dict[str, int] = Field(default_factory=dict)
    recommended_strategy: str = "none"  # "class_weight", "smote", "resample", "threshold_tuning"
    recommended_metric: str = "roc_auc"  # "pr_auc", "f1", "balanced_accuracy"
    description: str = ""


class ImbalanceAgent(BaseAgent):
    """Detects and resolves target class imbalances with safe deterministic techniques."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ImbalanceAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        dataset_path = input_data.dataset_path or input_data.parameters.get("dataset_path")
        target_column = input_data.parameters.get("target_column")

        if not dataset_path or not target_column:
            return AgentOutput(
                success=True,
                data=ImbalanceAnalysisResult(description="No target column or dataset provided").model_dump(),
                message="No target column provided to evaluate class balance",
            )

        try:
            df = pd.read_csv(dataset_path)
            if target_column not in df.columns:
                return AgentOutput(
                    success=False,
                    errors=[f"Target '{target_column}' not found in dataset"],
                )

            counts = df[target_column].value_counts()
            if len(counts) <= 1:
                return AgentOutput(
                    success=True,
                    data=ImbalanceAnalysisResult(
                        is_imbalanced=False,
                        class_counts={str(k): int(v) for k, v in counts.items()},
                        description="Single class present",
                    ).model_dump(),
                )

            total = len(df)
            min_count = counts.min()
            max_count = counts.max()
            minority_pct = round((min_count / total) * 100, 2)
            ratio = round(max_count / max(min_count, 1), 2)
            minority_class = counts.idxmin()

            is_imbalanced = ratio >= 3.0 or minority_pct <= 20.0
            
            # Select mitigation strategy
            if ratio >= 20.0 or minority_pct <= 2.0:
                strategy = "class_weight_and_threshold"
                metric = "pr_auc"
                desc = f"Extreme class imbalance detected ({minority_pct}% minority). Use PR-AUC, class weights, and threshold tuning."
            elif is_imbalanced:
                strategy = "class_weight"
                metric = "f1"
                desc = f"Moderate class imbalance detected ({minority_pct}% minority). Use class weights and balanced scoring."
            else:
                strategy = "none"
                metric = "accuracy"
                desc = f"Balanced classes ({minority_pct}% minority)."

            result = ImbalanceAnalysisResult(
                is_imbalanced=is_imbalanced,
                imbalance_ratio=ratio,
                minority_class=str(minority_class),
                minority_percentage=minority_pct,
                class_counts={str(k): int(v) for k, v in counts.items()},
                recommended_strategy=strategy,
                recommended_metric=metric,
                description=desc,
            )

            return AgentOutput(
                success=True,
                data=result.model_dump(),
                message=desc,
            )
        except Exception as e:
            logger.error(f"[ImbalanceAgent] Error: {e}")
            return AgentOutput(success=False, errors=[str(e)])
