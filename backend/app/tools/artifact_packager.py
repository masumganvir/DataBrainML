"""
DataWise AI — Production Model Serializer, Metadata & Artifact Packager

Handles:
  1. Serializing the final Pipeline object with joblib (preprocessor + model together).
  2. Generating comprehensive model_metadata.json (dataset hash, scores, versions, features).
  3. Generating standalone executable inference.py, preprocessing.py, and training.py.
  4. Packaging complete downloadable ZIP bundle adhering to Section 34 specifications.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.pipeline import Pipeline

from app.config.settings import get_settings

settings = get_settings()


class ArtifactPackager:
    """
    Manages export of production model artifacts, metadata, and executable Python scripts.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = settings.artifacts_dir_path / session_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Structure matching Section 34
        self.project_dir = self.base_dir / "DataWise_Project"
        self.model_dir = self.project_dir / "model"
        self.code_dir = self.project_dir / "code"
        self.report_dir = self.project_dir / "report"
        self.notebook_dir = self.project_dir / "notebook"
        self.viz_dir = self.project_dir / "visualizations"

        for d in [self.model_dir, self.code_dir, self.report_dir, self.notebook_dir, self.viz_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def serialize_model(self, pipeline: Pipeline) -> str:
        """Serializes the end-to-end preprocessing + model Pipeline using joblib."""
        model_path = self.model_dir / "final_model.joblib"
        joblib.dump(pipeline, model_path)
        logger.info(f"Final model pipeline successfully serialized to {model_path}")
        return str(model_path)

    def generate_metadata(
        self,
        target_col: str,
        task_type: str,
        model_name: str,
        num_cols: List[str],
        cat_cols: List[str],
        cv_scores: List[float],
        test_metrics: Dict[str, float],
        dataset_path: Optional[str] = None,
    ) -> str:
        """Saves exhaustive model_metadata.json with library versions and dataset hash."""
        # Calculate dataset SHA256 hash if available
        dataset_hash = "N/A"
        if dataset_path and os.path.exists(dataset_path):
            with open(dataset_path, "rb") as f:
                dataset_hash = hashlib.sha256(f.read()).hexdigest()

        metadata = {
            "project_name": "DataWise AI Production Model",
            "session_id": self.session_id,
            "version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "task_type": task_type,
            "target_column": target_col,
            "selected_model_architecture": model_name,
            "feature_schema": {
                "numerical_features": num_cols,
                "categorical_features": cat_cols,
                "total_features": len(num_cols) + len(cat_cols),
            },
            "preprocessing": {
                "numerical_imputer": "SimpleImputer(strategy='median')",
                "numerical_scaler": "StandardScaler()",
                "categorical_imputer": "SimpleImputer(strategy='most_frequent')",
                "categorical_encoder": "OneHotEncoder(handle_unknown='ignore')",
            },
            "evaluation": {
                "cv_scores": cv_scores,
                "cv_mean": round(float(np.mean(cv_scores)), 4) if cv_scores else 0.0,
                "cv_std": round(float(np.std(cv_scores)), 4) if cv_scores else 0.0,
                "test_metrics": test_metrics,
            },
            "dataset_sha256": dataset_hash,
            "system_environment": {
                "python_version": platform.python_version(),
                "os": platform.system(),
                "scikit_learn_version": joblib.__name__,
            },
            "random_seed": 42,
        }

        meta_path = self.model_dir / "model_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return str(meta_path)

    def generate_inference_script(
        self,
        target_col: str,
        task_type: str,
        is_classification: bool = True,
    ) -> str:
        """Generates production inference.py script directly loading final_model.joblib."""
        code = f'''"""
DataWise AI — Production Inference Script
Generated automatically for target: {target_col} ({task_type})
"""

import sys
import json
from pathlib import Path
import pandas as pd
import joblib

MODEL_PATH = Path(__file__).parent.parent / "model" / "final_model.joblib"
METADATA_PATH = Path(__file__).parent.parent / "model" / "model_metadata.json"


def load_model():
    """Loads the serialized end-to-end scikit-learn pipeline."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model artifact not found at {{MODEL_PATH}}")
    return joblib.load(MODEL_PATH)


def predict(data_source):
    """
    Accepts a pandas DataFrame or path to a CSV file.
    Executes end-to-end preprocessing, scaling, encoding, and inference.
    """
    if isinstance(data_source, (str, Path)):
        df = pd.read_csv(data_source)
    elif isinstance(data_source, pd.DataFrame):
        df = data_source.copy()
    else:
        raise TypeError("Expected filepath or pandas DataFrame.")

    # Drop target column if present in evaluation input
    if "{target_col}" in df.columns:
        df = df.drop(columns=["{target_col}"])

    model = load_model()
    predictions = model.predict(df)
    results = pd.DataFrame({{"prediction": predictions}})

    # Generate probabilities for classification
    if hasattr(model, "predict_proba"):
        try:
            probas = model.predict_proba(df)
            if probas.shape[1] == 2:
                results["probability_positive"] = probas[:, 1]
            else:
                for i in range(probas.shape[1]):
                    results[f"probability_class_{{i}}"] = probas[:, i]
        except Exception:
            pass

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inference.py <path_to_new_data.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    print(f"Loading data from {{csv_path}}...")
    preds = predict(csv_path)
    print("\\n=== Inference Results (first 10 rows) ===")
    print(preds.head(10))
    output_path = "predictions_output.csv"
    preds.to_csv(output_path, index=False)
    print(f"\\nSaved full predictions to {{output_path}}")
'''
        script_path = self.code_dir / "inference.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code.strip())

        return str(script_path)

    def generate_preprocessing_script(
        self,
        num_cols: List[str],
        cat_cols: List[str],
    ) -> str:
        """Generates standalone preprocessing.py module."""
        code = f'''"""
DataWise AI — Preprocessing Pipeline Definition
"""

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

NUMERICAL_FEATURES = {num_cols}
CATEGORICAL_FEATURES = {cat_cols}


def create_preprocessor() -> ColumnTransformer:
    """Builds leak-free ColumnTransformer for numerical and categorical features."""
    transformers = []
    if NUMERICAL_FEATURES:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("num", num_pipe, NUMERICAL_FEATURES))

    if CATEGORICAL_FEATURES:
        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
        transformers.append(("cat", cat_pipe, CATEGORICAL_FEATURES))

    return ColumnTransformer(transformers=transformers, remainder="drop")
'''
        script_path = self.code_dir / "preprocessing.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code.strip())

        return str(script_path)

    def generate_training_script(
        self,
        target_col: str,
        task_type: str,
        model_name: str,
    ) -> str:
        """Generates standalone training.py script."""
        code = f'''"""
DataWise AI — Training Script
Reproduces training of {model_name} on clean data.
"""

import sys
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from preprocessing import create_preprocessor

TARGET_COL = "{target_col}"
TASK_TYPE = "{task_type}"


def train(data_path: str):
    df = pd.read_csv(data_path)
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    preprocessor = create_preprocessor()
    # Replace with selected estimator architecture
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    estimator = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42) if TASK_TYPE == "classification" else RandomForestRegressor(n_estimators=50, random_state=42)

    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    print("Training pipeline...")
    pipe.fit(X_train, y_train)
    score = pipe.score(X_test, y_test)
    print(f"Test Score: {{round(score, 4)}}")

    joblib.dump(pipe, "retrained_model.joblib")
    print("Model saved to retrained_model.joblib")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python training.py <path_to_dataset.csv>")
        sys.exit(1)
    train(sys.argv[1])
'''
        script_path = self.code_dir / "training.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code.strip())

        return str(script_path)

    def generate_readme(
        self,
        target_col: str,
        task_type: str,
        best_model: str,
        metrics: Dict[str, float],
    ) -> str:
        """Creates README.md describing the exported project package."""
        metric_lines = "\n".join([f"- **{k}**: {v}" for k, v in metrics.items()])
        content = f"""# DataWise AI — Production Model Package

## Project Overview
- **Session ID**: `{self.session_id}`
- **Task Type**: `{task_type}`
- **Target Feature**: `{target_col}`
- **Final Selected Model**: `{best_model}`

## Performance Metrics (Test Set)
{metric_lines}

## Package Structure
```text
DataWise_Project/
├── report/
│   └── analysis_report.html       # Full interactive analysis & diagnostic report
├── notebook/
│   └── dataset_analysis.ipynb     # Complete 24-section reproducible Jupyter Notebook
├── model/
│   ├── final_model.joblib         # Scikit-learn Pipeline (preprocessing + model)
│   └── model_metadata.json        # Reproducibility metadata, versions, hash
├── code/
│   ├── preprocessing.py           # Standalone preprocessing transformer
│   ├── training.py                # Standalone training script
│   └── inference.py               # Standalone production inference script
└── README.md
```

## Running Inference
```bash
pip install pandas scikit-learn joblib
python code/inference.py path/to/new_data.csv
```
"""
        readme_path = self.project_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content.strip())

        return str(readme_path)

    def create_zip_bundle(self) -> str:
        """Zips the DataWise_Project directory into a single downloadable ZIP archive."""
        zip_path = self.base_dir / f"DataWise_Project_{self.session_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.project_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.base_dir)
                    zipf.write(file_path, arcname)

        logger.info(f"Project bundle successfully packaged: {zip_path}")
        return str(zip_path)


def generate_fastapi_service_code(
    model_name: str = "final_model",
    target_col: Any = "target",
    feature_columns: Optional[List[str]] = None,
) -> str:
    if isinstance(target_col, (list, tuple)):
        feature_columns = list(target_col)
        target_col = "target"
    cols = feature_columns or ["feature_1", "feature_2"]

    return f'''import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Model Serving API - {model_name}", version="1.0.0")

model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        model = joblib.load("model/final_model.joblib")
    except Exception as e:
        print(f"Error loading model: {{e}}")

class PredictionPayload(BaseModel):
    data: List[Dict[str, Any]]

@app.get("/health")
def health():
    return {{"status": "ok", "model_loaded": model is not None}}

@app.get("/model-info")
def model_info():
    return {{"model_name": "{model_name}", "target": "{target_col}", "features": {cols}}}

# POST /predict inference endpoint
@app.post("/predict")
def predict(payload: PredictionPayload):
    if model is None:

        raise HTTPException(status_code=503, detail="Model not loaded")
    df = pd.DataFrame(payload.data)
    predictions = model.predict(df).tolist()
    return {{"predictions": predictions, "model_version": "v1.0.0"}}
'''.strip()


def generate_dockerfile_content(python_version: str = "3.11-slim") -> str:
    return f'''FROM python:{python_version}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]
'''.strip()


def generate_requirements_txt(extra_packages: Optional[List[str]] = None) -> str:
    pkgs = ["fastapi", "uvicorn", "pandas", "numpy", "scikit-learn", "joblib", "pydantic"]
    if extra_packages:
        pkgs.extend(extra_packages)
    return "\n".join(sorted(list(set(pkgs))))


def generate_model_metadata_json(
    session_id: str,
    target_col: str,
    task_type: str,
    best_model: str,
    metrics: Dict[str, float],
    feature_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "target_col": target_col,
        "task_type": task_type,
        "best_model": best_model,
        "metrics": metrics,
        "feature_columns": feature_columns or [],
        "created_at": datetime.datetime.utcnow().isoformat(),
    }


def validate_inference_payload(payload: Dict[str, Any], expected_features: List[str]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"valid": False, "error": "Payload must be a dictionary"}
    data = payload.get("data", [])
    if not isinstance(data, list) or len(data) == 0:
        return {"valid": False, "error": "Payload must contain a non-empty 'data' list"}
    first_row = data[0]
    missing_cols = [c for c in expected_features if c not in first_row]
    return {
        "valid": len(missing_cols) == 0,
        "missing_features": missing_cols,
        "row_count": len(data),
    }


def package_model_artifact(
    session_id: str,
    pipeline: Any,
    target_col: str,
    task_type: str,
    best_model: str,
    metrics: Dict[str, float],
    feature_columns: Optional[List[str]] = None,
) -> Dict[str, str]:
    packager = ArtifactPackager(session_id)
    if hasattr(pipeline, "fit") or isinstance(pipeline, Pipeline):
        model_path = packager.serialize_model(pipeline)
    else:
        model_path = str(packager.model_dir / "final_model.joblib")
    readme_path = packager.generate_readme(target_col, task_type, best_model, metrics)
    zip_path = packager.create_zip_bundle()
    return {
        "model_path": model_path,
        "readme_path": readme_path,
        "zip_path": zip_path,
    }

