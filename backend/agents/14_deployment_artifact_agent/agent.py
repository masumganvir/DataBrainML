"""
DataWise AI — Agent 14: Deployment Artifact Agent Implementation
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline

from .schemas import AgentInput, AgentOutput
from tools.preprocessing import build_column_transformer, split_dataset
from tools.serialization import save_pipeline, generate_model_metadata, FastAPIServiceGenerator


class ArtifactAgent:
    """Agent 14: Serializes champion pipeline, metadata, standalone inference script, and FastAPI service."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Deployment & Artifact Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                path = input_data.dataset_path
                ext = Path(path).suffix.lower()
                if ext in (".xlsx", ".xls"):
                    df = pd.read_excel(path)
                elif ext == ".json":
                    df = pd.read_json(path)
                else:
                    df = pd.read_csv(path, low_memory=False)

                target = input_data.parameters.get("target_column")
                task = input_data.parameters.get("task_type", "classification")

                if not target or target not in df.columns:
                    target = df.columns[-1]

                X_train, X_test, y_train, y_test = split_dataset(
                    df,
                    target_column=target,
                    test_size=0.2,
                    stratify=(task == "classification"),
                )

                num_cols = list(X_train.select_dtypes(include=[np.number]).columns)
                cat_cols = list(X_train.select_dtypes(exclude=[np.number]).columns)
                preprocessor = build_column_transformer(num_cols, cat_cols)

                model = (
                    RandomForestClassifier(n_estimators=100, random_state=42)
                    if task == "classification"
                    else RandomForestRegressor(n_estimators=100, random_state=42)
                )

                pipe = Pipeline([("prep", preprocessor), ("model", model)])
                pipe.fit(X_train, y_train)

                test_score = float(pipe.score(X_test, y_test))

                # Output artifact paths
                out_dir = Path("artifacts") / input_data.session_id
                out_dir.mkdir(parents=True, exist_ok=True)

                model_file = str(out_dir / "final_model.joblib")
                meta_file = str(out_dir / "model_metadata.json")
                inference_file = str(out_dir / "inference.py")
                api_dir = out_dir / "api"

                # 1. Save pipeline
                save_pipeline(pipe, model_file)

                # 2. Save metadata
                generate_model_metadata(
                    model_name=model.__class__.__name__,
                    target_column=target,
                    feature_names=list(X_train.columns),
                    task_type=task,
                    metrics={"test_score": round(test_score, 4)},
                    hyperparameters={"n_estimators": 100, "random_state": 42},
                    output_path=meta_file,
                )

                # 3. Save inference.py
                inference_code = f"""# Standalone Inference Script
import joblib
import pandas as pd

def predict(input_data):
    model = joblib.load('final_model.joblib')
    if isinstance(input_data, dict):
        input_data = pd.DataFrame([input_data])
    return model.predict(input_data)

if __name__ == '__main__':
    print("Inference module ready.")
"""
                with open(inference_file, "w", encoding="utf-8") as f:
                    f.write(inference_code)

                # 4. Generate FastAPI microservice
                api_gen = FastAPIServiceGenerator(
                    model_path=model_file,
                    metadata_path=meta_file,
                    features=list(X_train.columns),
                    target_column=target,
                    task_type=task,
                )
                api_path = api_gen.generate(str(api_dir))

                summary = (
                    f"Deployment Artifact Agent generated: 'final_model.joblib', "
                    "'model_metadata.json', 'inference.py', and complete FastAPI microservice."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "model_path": model_file,
                        "metadata_path": meta_file,
                        "inference_script_path": inference_file,
                        "api_service_path": api_path,
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "save_pipeline", "status": "ready"},
                summary="Deployment Artifact Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Deployment Artifact Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Deployment Artifact Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
