"""
DataWise AI — Reproducibility & Provenance Logger
Implements Prompt Section 55 & 56:
- Calculates SHA-256 cryptographic hash of input dataset
- Captures environment: Python version, OS platform, package versions
- Records random seed, model parameters, and preprocessing decisions
- Outputs structured reproducibility.json
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
import sklearn


def generate_reproducibility_artifact(
    dataset_path: Optional[str],
    output_dir: Path,
    random_seed: int = 42,
    model_name: Optional[str] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    preprocessing_steps: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Computes dataset checksum and records complete runtime environment
    into reproducibility.json.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "reproducibility.json"

    dataset_hash = "N/A"
    file_size_bytes = 0
    if dataset_path and os.path.exists(dataset_path):
        try:
            file_size_bytes = os.path.getsize(dataset_path)
            sha256 = hashlib.sha256()
            with open(dataset_path, "rb") as f:
                while chunk := f.read(65536):
                    sha256.update(chunk)
            dataset_hash = sha256.hexdigest()
        except Exception:
            pass

    reproducibility_data = {
        "reproducibility_version": "1.0.0",
        "random_seed": random_seed,
        "dataset": {
            "source_path": dataset_path,
            "sha256_hash": dataset_hash,
            "size_bytes": file_size_bytes,
        },
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "os_name": os.name,
            "packages": {
                "scikit-learn": sklearn.__version__,
                "pandas": pd.__version__,
                "numpy": np.__version__,
                "joblib": joblib.__version__,
            },
        },
        "model_spec": {
            "champion_model": model_name,
            "hyperparameters": hyperparameters or {},
            "preprocessing": preprocessing_steps or {},
        },
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(reproducibility_data, f, indent=2)

    return reproducibility_data
