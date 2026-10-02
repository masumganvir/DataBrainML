"""
DataWise AI — Deployment Agent
Generates deployment files: Dockerfile, prediction_example.py, OpenAPI schema, and README.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput


class DeploymentAgent(BaseAgent):
    """Generates deployable inference code and container manifests."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id)
        self.agent_name = "Deployment Agent"

    def run(self, input_data: AgentInput) -> AgentOutput:
        try:
            params = input_data.parameters or {}
            output_dir = Path(params.get("output_dir", f"artifacts/{self.session_id}/deployment"))
            output_dir.mkdir(parents=True, exist_ok=True)

            target_col = params.get("target_column", "target")
            features = params.get("features", ["feature_1"])

            # 1. prediction_example.py
            pred_script = f"""# Standalone Model Serving & Prediction Example
import joblib
import pandas as pd
import numpy as np

# 1. Load Serialized Pipeline
pipeline = joblib.load('../models/model_pipeline.pkl')
print("Successfully loaded model_pipeline.pkl")

# 2. Sample Inference Payload
sample_row = pd.DataFrame([{{
    {", ".join([f'"{f}": 0' for f in features[:6]])}
}}])

# 3. Predict
pred = pipeline.predict(sample_row)
print(f"Prediction output for {target_col}: {{pred[0]}}")
if hasattr(pipeline, "predict_proba"):
    print(f"Probabilities: {{pipeline.predict_proba(sample_row)}}")
"""
            with open(output_dir / "prediction_example.py", "w", encoding="utf-8") as f:
                f.write(pred_script)

            # 2. Dockerfile
            dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
            with open(output_dir / "Dockerfile", "w", encoding="utf-8") as f:
                f.write(dockerfile)

            # 3. api_schema.json
            api_schema = {
                "openapi": "3.0.0",
                "info": {"title": "Model Prediction API", "version": "1.0.0"},
                "paths": {
                    "/predict": {
                        "post": {
                            "summary": "Run Inference",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {"features": {"type": "object"}},
                                        }
                                    }
                                }
                            },
                            "responses": {"200": {"description": "Inference Result"}},
                        }
                    }
                },
            }
            with open(output_dir / "api_schema.json", "w", encoding="utf-8") as f:
                json.dump(api_schema, f, indent=2)

            # 4. README.md
            with open(output_dir / "README.md", "w", encoding="utf-8") as f:
                f.write("# Production Deployment Instructions\n\nRun `python prediction_example.py` to test the pipeline locally.\n")

            return AgentOutput(
                session_id=self.session_id,
                agent_name=self.agent_name,
                status="success",
                message="Generated deployment artifacts (Dockerfile, prediction_example.py, api_schema.json).",
                artifacts_generated=[
                    str(output_dir / "prediction_example.py"),
                    str(output_dir / "Dockerfile"),
                    str(output_dir / "api_schema.json"),
                    str(output_dir / "README.md"),
                ],
            )
        except Exception as exc:
            return AgentOutput(session_id=self.session_id, agent_name=self.agent_name, status="error", message=str(exc))
