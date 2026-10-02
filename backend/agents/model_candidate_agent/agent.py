"""
DataWise AI — ModelCandidateAgent (Section 19)
Analyzes dataset characteristics (n_samples, n_features, sparsity, imbalance, latency requirements)
and selects appropriate model families without blind brute-force training.
"""

from __future__ import annotations

from typing import Any, Dict, List
from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.model_selection.agent import ModelSelectionAgent


class ModelCandidateAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelCandidateAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        return ModelSelectionAgent(session_id=input_data.session_id).analyze(input_data)
