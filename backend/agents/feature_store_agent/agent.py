"""
Agentic AutoML Intelligence Platform — Feature Store Agent
Manages feature registration, online retrieval, and offline training dataset generation.
"""

from __future__ import annotations

from agents.base import BaseAgent, AgentInput, AgentOutput
from feature_store.schemas import FeatureDefinition
from feature_store.store import feature_store


class FeatureStoreAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FeatureStoreAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        action = input_data.parameters.get("action", "list")

        if action == "register":
            definition_data = input_data.parameters.get("definition", {})
            definition = FeatureDefinition(**definition_data)
            feature_store.register_feature(definition)
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=definition.model_dump(),
                summary=f"Registered feature '{definition.feature_name}' (v{definition.version})",
            )
        elif action == "get_online":
            entity_id = input_data.parameters.get("entity_id", "")
            features = feature_store.get_online_features(entity_id)
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=features.model_dump() if features else {},
                summary=f"Retrieved online features for entity '{entity_id}'.",
            )
        else:
            # Default action: list features
            features = [f.model_dump() for f in feature_store.list_features()]
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"features": features, "total": len(features)},
                summary=f"Feature catalog contains {len(features)} registered features.",
            )
