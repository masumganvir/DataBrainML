"""
DataWise AI — HyperparameterOptimizationAgent
Conducts Optuna Bayesian optimization with pruning and time budgets.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from agents.hyperparameter_optimization_agent.schemas import HyperparameterOptimizationAgentInput, HyperparameterOptimizationAgentResult


class HyperparameterOptimizationAgent(BaseAgent):
    """HyperparameterOptimizationAgent: Conducts Optuna Bayesian optimization with pruning and time budgets."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="HyperparameterOptimizationAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        from agents.hyperparameter_tuning.agent import HyperparameterTuningAgent; return HyperparameterTuningAgent(session_id=input_data.session_id).analyze(input_data)
