"""
Agentic AutoML Intelligence Platform — Online Learning Agent
Performs safe incremental partial_fit updates and policy-guided model adaptation.
"""

from __future__ import annotations

import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from ml.online_learning import ContinuousLearningPolicy, online_learning_engine
from deployment.shadow_manager import deployment_manager


class OnlineLearningAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="OnlineLearningAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        model = input_data.parameters.get("model")
        if model is None and deployment_manager.active_version:
            model = deployment_manager._version_registry.get(deployment_manager.active_version)

        if model is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message="No model available for incremental online update.",
            )

        # Check incremental support
        if not online_learning_engine.supports_incremental_learning(model):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                data={"supported": False, "algorithm": type(model).__name__},
                summary=f"Algorithm '{type(model).__name__}' does not support partial_fit online updates.",
            )

        X_new = input_data.parameters.get("X_new")
        y_new = input_data.parameters.get("y_new")
        val_X = input_data.parameters.get("val_X")
        val_y = input_data.parameters.get("val_y")

        if X_new is None or y_new is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"supported": True, "algorithm": type(model).__name__},
                summary=f"Algorithm '{type(model).__name__}' supports incremental online learning.",
            )

        updated_model, update_res = online_learning_engine.execute_incremental_update(
            current_model=model,
            X_new=pd.DataFrame(X_new),
            y_new=pd.Series(y_new),
            validation_X=pd.DataFrame(val_X) if val_X is not None else None,
            validation_y=pd.Series(val_y) if val_y is not None else None,
            policy=ContinuousLearningPolicy(input_data.parameters.get("policy", "INCREMENTAL")),
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if update_res.success else "error",
            data=update_res.to_dict(),
            summary=update_res.message,
        )
