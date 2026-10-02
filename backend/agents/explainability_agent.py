"""
DataWise AI — Explainability Agent
Computes feature importances and model interpretability.
"""

from __future__ import annotations

import numpy as np
from agents.base import BaseAgent, AgentInput, AgentOutput


class ExplainabilityAgent(BaseAgent):
    """Provides feature attribution and model transparency."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Explainability Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        feature_names = params.get("feature_names", [])
        pipeline = params.get("pipeline")

        importances = []
        if pipeline and hasattr(pipeline, "named_steps"):
            model = pipeline.named_steps.get("model")
            if hasattr(model, "feature_importances_"):
                raw_imp = model.feature_importances_
                for i, score in enumerate(raw_imp):
                    feat_name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
                    importances.append({"feature": feat_name, "importance": round(float(score), 4)})
                importances.sort(key=lambda x: x["importance"], reverse=True)

        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=f"Computed feature importances for {len(importances)} features.",
            data={"feature_importances": importances[:15]},
        )
