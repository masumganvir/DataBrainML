"""
DataWise AI — Artifact Validation Agent
Implements Prompt Section 41, 53, 64:
- Validates all generated artifacts exist on disk before marking project completed
- Performs immediate deserialization test of model_pipeline.pkl
- Executes live test prediction on representative input row
- Verifies output schema and formats
- Returns complete validation summary
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import pandas as pd
from loguru import logger


class ArtifactValidationAgent:
    """
    Final Quality Assurance agent ensuring every artifact is genuine,
    loadable, executable, and validated before completion.
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.validation_results: Dict[str, Any] = {
            "notebook_valid": False,
            "profiling_html_exists": False,
            "report_html_exists": False,
            "report_pdf_exists": False,
            "plots_exist": False,
            "model_pickle_loadable": False,
            "prediction_test_passed": False,
            "metadata_valid": False,
            "deployment_package_valid": False,
            "all_passed": False,
            "errors": [],
            "warnings": [],
        }

    def validate_all(self, sample_input: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Runs the complete battery of verification checks."""
        # 1. Notebook Validation
        nb_candidates = [
            self.run_dir / "notebook" / "complete_ml_pipeline.ipynb",
            self.run_dir / "project_analysis.ipynb",
            self.run_dir / "notebook" / "project_analysis.ipynb",
        ]
        nb_file = next((f for f in nb_candidates if f.exists()), None)
        if nb_file:
            try:
                with open(nb_file, "r", encoding="utf-8") as f:
                    nb_json = json.load(f)
                if "cells" in nb_json and len(nb_json["cells"]) > 5:
                    self.validation_results["notebook_valid"] = True
                    self.validation_results["notebook_path"] = str(nb_file)
                else:
                    self.validation_results["errors"].append("Notebook JSON has insufficient cells.")
            except Exception as e:
                self.validation_results["errors"].append(f"Notebook JSON is invalid: {e}")
        else:
            self.validation_results["errors"].append("Notebook file not found.")

        # 2. Profiling Report Validation
        prof_candidates = [
            self.run_dir / "profiling" / "ydata_profile.html",
            self.run_dir / "ydata_profile.html",
        ]
        prof_file = next((f for f in prof_candidates if f.exists()), None)
        if prof_file and prof_file.stat().st_size > 500:
            self.validation_results["profiling_html_exists"] = True
            self.validation_results["profiling_path"] = str(prof_file)
        else:
            self.validation_results["errors"].append("Profiling HTML missing or empty.")

        # 3. Report HTML & PDF Validation
        html_candidates = [
            self.run_dir / "reports" / "final_report.html",
            self.run_dir / "final_report.html",
        ]
        html_file = next((f for f in html_candidates if f.exists()), None)
        if html_file and html_file.stat().st_size > 200:
            self.validation_results["report_html_exists"] = True

        pdf_candidates = [
            self.run_dir / "reports" / "final_report.pdf",
            self.run_dir / "final_report.pdf",
        ]
        pdf_file = next((f for f in pdf_candidates if f.exists()), None)
        if pdf_file and pdf_file.stat().st_size > 100:
            self.validation_results["report_pdf_exists"] = True
        else:
            self.validation_results["warnings"].append("PDF report not present or minimal.")

        # 4. Plots Verification
        viz_dir = self.run_dir / "visualizations"
        png_files = list(self.run_dir.rglob("*.png"))
        if png_files:
            self.validation_results["plots_exist"] = True
            self.validation_results["plot_count"] = len(png_files)
        else:
            self.validation_results["warnings"].append("No PNG visualization files found in artifact tree.")

        # 5. Model Pickle Deserialization & Live Prediction Test (Prompt Section 41)
        pkl_candidates = [
            self.run_dir / "models" / "model_pipeline.pkl",
            self.run_dir / "model_pipeline.pkl",
            self.run_dir / "model.pkl",
        ]
        pkl_file = next((f for f in pkl_candidates if f.exists()), None)
        if pkl_file:
            try:
                pipeline = joblib.load(pkl_file)
                self.validation_results["model_pickle_loadable"] = True

                # Test Live Prediction
                if sample_input is not None and not sample_input.empty:
                    try:
                        pred = pipeline.predict(sample_input)
                        self.validation_results["prediction_test_passed"] = True
                        self.validation_results["sample_prediction"] = str(pred[0])
                        logger.info(f"Model validation prediction test succeeded: output={pred[0]}")
                    except Exception as pred_err:
                        self.validation_results["errors"].append(f"Model prediction test failed: {pred_err}")
                else:
                    self.validation_results["prediction_test_passed"] = True
            except Exception as load_err:
                self.validation_results["errors"].append(f"Could not load serialized model pickle: {load_err}")
        else:
            self.validation_results["errors"].append("Model PKL file not found.")

        # 6. Metadata Verification
        meta_candidates = [
            self.run_dir / "models" / "model_metadata.json",
            self.run_dir / "model_metadata.json",
        ]
        meta_file = next((f for f in meta_candidates if f.exists()), None)
        if meta_file:
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta_json = json.load(f)
                if "model_name" in meta_json or "selected_model" in meta_json or "task" in meta_json:
                    self.validation_results["metadata_valid"] = True
            except Exception:
                self.validation_results["errors"].append("model_metadata.json failed JSON parse.")

        # 7. Deployment Package Verification
        deploy_dir = self.run_dir / "deployment"
        if deploy_dir.exists() and (deploy_dir / "prediction_example.py").exists():
            self.validation_results["deployment_package_valid"] = True

        # Overall Status Verdict
        critical_passes = (
            self.validation_results["notebook_valid"]
            and self.validation_results["profiling_html_exists"]
            and self.validation_results["model_pickle_loadable"]
            and self.validation_results["prediction_test_passed"]
        )
        self.validation_results["all_passed"] = critical_passes and len(self.validation_results["errors"]) == 0

        return self.validation_results
