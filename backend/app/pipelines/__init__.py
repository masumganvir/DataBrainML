"""
DataWise AI — Pipelines Module
End-to-end deterministic execution pipelines.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
import pandas as pd
from loguru import logger

from app.tools.data_tools import load_dataset_file, profile_dataset
from app.tools.target_detector import detect_target_column, classify_problem_type
from app.tools.ml_tools import ModelTrainer
from app.tools.artifact_packager import package_model_artifact


class EndToEndAutoMLPipeline:
    """
    Executes a complete, leak-free, deterministic AutoML workflow:
    Ingestion -> Profiling -> Preprocessing -> Model Training -> Evaluation -> Packaging.
    """
    def __init__(self, dataset_path: str, target_column: Optional[str] = None):
        self.dataset_path = dataset_path
        self.target_column = target_column

    def run(self) -> Dict[str, Any]:
        logger.info(f"Starting AutoML pipeline for dataset: {self.dataset_path}")
        df = load_dataset_file(self.dataset_path)

        # 1. Profile
        profile = profile_dataset(self.dataset_path)

        # 2. Target & Task detection
        if not self.target_column:
            target_res = detect_target_column(df)
            self.target_column = target_res.get("target_column")

        pt_res = classify_problem_type(df, self.target_column)
        problem_type = pt_res.get("problem_type", "classification")

        # 3. Model Training
        trainer = ModelTrainer(df=df, target_col=self.target_column, task_type=problem_type)
        train_results = trainer.train_and_evaluate()

        # 4. Packaging
        best_name = train_results["best_model_name"]
        best_pipe = train_results["best_pipeline"]
        pkg_res = package_model_artifact(
            best_pipe,
            model_name=best_name,
            features=train_results.get("numerical_features", []) + train_results.get("categorical_features", []),
            metrics=train_results.get("trained_models", [{}])[0].get("test_metrics", {})
        )

        return {
            "dataset_rows": len(df),
            "target_column": self.target_column,
            "problem_type": problem_type,
            "best_model_name": best_name,
            "metrics": train_results.get("trained_models", [{}])[0].get("test_metrics", {}),
            "packaged_artifacts": pkg_res,
            "status": "success"
        }


__all__ = ["EndToEndAutoMLPipeline"]
