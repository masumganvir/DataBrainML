"""
Agentic AutoML Intelligence Platform — Model Packaging Agent
Packages trained models, ONNX binaries, preprocessors, input/output schemas, and Docker assets.
"""

from __future__ import annotations

import json
from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.artifact_packager import package_model_artifacts


class ModelPackagingAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelPackagingAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        model = input_data.parameters.get("model")
        features = input_data.parameters.get("features", [])
        metrics = input_data.parameters.get("metrics", {})
        model_name = input_data.parameters.get("model_name", "production_model")

        if model is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message="No model provided for packaging.",
            )

        try:
            artifact_bundle = package_model_artifacts(
                model=model,
                feature_names=features,
                metrics=metrics,
                model_name=model_name,
            )

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=artifact_bundle,
                summary=f"Model successfully packaged with ONNX/Joblib, schemas, requirements, and deployment assets.",
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message=f"Model packaging failed: {str(e)}",
            )
