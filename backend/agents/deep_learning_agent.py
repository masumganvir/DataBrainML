"""
DataWise AI — Deep Learning Agent
Evaluates neural network architectures where justified by dataset scale or unstructured data.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput


class DeepLearningAgent(BaseAgent):
    """Evaluates suitability of neural network models."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Deep Learning Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        n_samples = params.get("n_samples", 1000)
        is_tabular = params.get("is_tabular", True)

        if is_tabular and n_samples < 50000:
            recommendation = "Tabular data under 50k rows: Tree-based ensembles (RandomForest, HistGradientBoosting) strongly outperform deep networks with zero hyperparameter fragility."
            suitable = False
        else:
            recommendation = "Large scale or multi-modal dataset: MLP / Deep architectures recommended."
            suitable = True

        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=recommendation,
            data={"suitable": suitable, "rationale": recommendation},
        )
