"""
Agentic AutoML Intelligence Platform — Realtime Prediction Agent
Sub-millisecond inference execution with online feature enrichment and shadow comparison.
"""

from __future__ import annotations

import time
import pandas as pd
from agents.base import BaseAgent, AgentInput, AgentOutput
from feature_store.store import feature_store
from deployment.shadow_manager import deployment_manager


class RealtimePredictionAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="RealtimePredictionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        entity_id = input_data.parameters.get("entity_id", "")
        raw_features = input_data.parameters.get("features", {})
        feature_names = input_data.parameters.get("feature_names")

        # 1. Enrich from FeatureStore if entity_id is provided
        if entity_id:
            online_features = feature_store.get_online_features(entity_id, feature_names=feature_names)
            if online_features:
                raw_features = {**online_features.feature_values, **raw_features}

        # 2. Build input dataframe
        df = pd.DataFrame([raw_features])

        # 3. Execute prediction via deployment manager (with shadow evaluation)
        try:
            primary_pred, shadow_meta = deployment_manager.predict(df)
            pred_value = primary_pred.tolist() if hasattr(primary_pred, "tolist") else primary_pred

            res_data = {
                "entity_id": entity_id,
                "prediction": pred_value,
                "active_version": deployment_manager.active_version,
                "shadow_comparison": shadow_meta,
            }

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=res_data,
                summary=f"Inference complete: {pred_value} (model version: {deployment_manager.active_version})",
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                message=f"Prediction error: {str(e)}",
            )
