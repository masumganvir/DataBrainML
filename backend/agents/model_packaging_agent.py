"""
DataWise AI — Model Packaging Agent
Serializes real pipelines with joblib, generates schemas and metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import joblib
from agents.base import BaseAgent, AgentInput, AgentOutput


class ModelPackagingAgent(BaseAgent):
    """Serializes pipelines to model_pipeline.pkl and writes metadata."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Model Packaging Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            pipeline = params.get("pipeline")
            output_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/models"))
            output_dir.mkdir(parents=True, exist_ok=True)

            if pipeline is None:
                return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message="Missing pipeline to serialize")

            pkl_path = output_dir / "model_pipeline.pkl"
            joblib.dump(pipeline, pkl_path)

            # Metadata
            meta_path = output_dir / "model_metadata.json"
            metadata = {
                "model_name": params.get("model_name", "ChampionModel"),
                "task_type": params.get("task_type", "classification"),
                "target_column": params.get("target_column"),
                "metrics": params.get("metrics", {}),
                "features": params.get("features", []),
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message=f"Serialized model pipeline to {pkl_path.name}",
                data={"model_path": str(pkl_path), "metadata_path": str(meta_path)},
                artifacts_generated=[str(pkl_path), str(meta_path)],
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
