"""
DataWise AI — Master Orchestration
Supervisor agent governing end-to-end autonomous AutoML state transitions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class MasterSupervisorAgent(BaseAgent):
    """
    Supervises full multi-stage LangGraph workflow.
    Directs transitions between Understanding -> Preprocessing -> Modeling -> Optimization -> Evaluation -> Deployment.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="MasterSupervisorAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        current_stage = input_data.parameters.get("current_stage", "INGESTION")

        stage_order = [
            "INGESTION",
            "UNDERSTANDING",
            "QUALITY_ASSESSMENT",
            "EDA_VISUALIZATION",
            "PREPROCESSING",
            "FEATURE_ENGINEERING",
            "MODEL_STRATEGY",
            "MODEL_TRAINING",
            "OPTIMIZATION",
            "EVALUATION",
            "EXPLAINABILITY",
            "VALIDATION",
            "DEPLOYMENT",
            "MONITORING"
        ]

        try:
            curr_idx = stage_order.index(current_stage)
            next_stage = stage_order[curr_idx + 1] if curr_idx + 1 < len(stage_order) else "COMPLETED"
        except ValueError:
            next_stage = "UNDERSTANDING"

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "current_stage": current_stage,
                "next_recommended_stage": next_stage,
                "human_in_the_loop_required": current_stage in ["PREPROCESSING", "DEPLOYMENT"],
                "pipeline_progress_pct": round(((curr_idx + 1) / len(stage_order)) * 100, 1)
            },
            summary=f"Supervisor coordinated transition: {current_stage} -> {next_stage}."
        )


__all__ = ["MasterSupervisorAgent"]
