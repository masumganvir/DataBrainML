"""
DataWise AI — Serialization: Joblib Pipeline Serializer
"""

from pathlib import Path
from typing import Any
import joblib


def save_pipeline(pipeline: Any, output_path: str) -> str:
    """Serializes fitted pipeline to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, str(path), compress=3)
    return str(path.resolve())


def load_pipeline(model_path: str) -> Any:
    """Loads serialized pipeline from disk."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return joblib.load(str(path))
