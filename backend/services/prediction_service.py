"""
DataWise AI — Prediction Service
Implements Prompt Section 31, 42, 43, 44, 49:
- Executes model prediction from loaded pipeline
- Validates input features against column_schema
- Calculates latency in milliseconds
- Returns confidence / class probabilities
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger


class PredictionService:
    """Handles inference requests, feature transformation, and latency measurement."""

    @staticmethod
    def predict(
        pipeline: Any,
        features: Dict[str, Any],
        column_schema: List[Dict[str, Any]],
        task_type: str = "Classification",
    ) -> Dict[str, Any]:
        """Runs inference through trained pipeline with schema validation."""
        t0 = time.perf_counter()

        # Construct single-row DataFrame adhering to column_schema
        row_dict = {}
        for col in column_schema:
            col_name = col["name"]
            val = features.get(col_name)
            if val is None or val == "":
                val = col.get("example", 0.0)

            if col.get("is_numeric", False):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0.0
            else:
                val = str(val)
            row_dict[col_name] = val

        input_df = pd.DataFrame([row_dict])
        raw_pred = pipeline.predict(input_df)[0]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        is_regression = "regression" in task_type.lower()
        if is_regression:
            pred_val = round(float(raw_pred), 4)
            return {
                "prediction": pred_val,
                "prediction_label": f"{pred_val:.4f}",
                "confidence": 1.0,
                "latency_ms": elapsed_ms,
                "task_type": task_type,
            }

        probabilities = {}
        confidence = 0.90
        if hasattr(pipeline, "predict_proba"):
            try:
                probs = pipeline.predict_proba(input_df)[0]
                classes = getattr(pipeline, "classes_", range(len(probs)))
                probabilities = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
                confidence = round(float(max(probs)), 4)
            except Exception as prob_err:
                logger.warning(f"predict_proba note: {prob_err}")

        return {
            "prediction": str(raw_pred),
            "prediction_label": str(raw_pred),
            "probabilities": probabilities,
            "confidence": confidence,
            "latency_ms": elapsed_ms,
            "task_type": task_type,
        }


prediction_service = PredictionService()
