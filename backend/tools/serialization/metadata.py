"""
DataWise AI — Serialization: Model Metadata Generator (Section 23)
"""

import json
from pathlib import Path
import platform
import sys
import time
from typing import Any, Dict, List, Optional
import sklearn


def generate_model_metadata(
    model_name: str,
    target_column: str,
    feature_names: List[str],
    task_type: str,
    metrics: Dict[str, Any],
    hyperparameters: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates reproducible production model metadata."""
    metadata = {
        "model_name": model_name,
        "version": "1.0.0",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_column": target_column,
        "task_type": task_type,
        "features": feature_names,
        "feature_count": len(feature_names),
        "metrics": metrics,
        "hyperparameters": hyperparameters or {},
        "environment": {
            "python_version": sys.version.split()[0],
            "os": platform.system(),
            "sklearn_version": sklearn.__version__,
        },
        "random_seed": 42,
    }

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    return metadata
