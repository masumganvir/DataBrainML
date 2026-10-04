"""
DataWise AI — Feature Extraction Agent
Section 20 Specification:
Designs domain-derived candidate features:
- Numerical: Ratios, pairwise interaction terms, polynomial candidates (where justified)
- Datetime: Year, month, day, weekday, hour, elapsed time
- Categorical: Frequency encodings, target aggregations
- Text: TF-IDF vectorization recommendations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class FeatureExtractionAgent:
    """Plans and evaluates task-dependent engineered feature candidates."""

    def __init__(self, name: str = "FeatureExtractionAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            cat_cols = state.get("categorical_columns") or list(df.select_dtypes(exclude=[np.number]).columns)
            dt_cols = state.get("datetime_columns") or []
            target_col = state.get("target_column")
            features = [c for c in num_cols if c != target_col]

            candidate_extractions: List[Dict[str, Any]] = []

            # 1. Numerical Ratios & Products
            for i in range(min(5, len(features))):
                for j in range(i + 1, min(5, len(features))):
                    c1, c2 = features[i], features[j]
                    candidate_extractions.append({
                        "name": f"{c1}_ratio_{c2}",
                        "type": "numerical_ratio",
                        "inputs": [c1, c2],
                        "formula": f"({c1} + 1e-5) / ({c2} + 1e-5)",
                        "rationale": f"Relative scale of {c1} per unit of {c2}.",
                    })

            # 2. Datetime extractions
            for dt_col in dt_cols:
                candidate_extractions.extend([
                    {"name": f"{dt_col}_year", "type": "temporal", "source": dt_col, "component": "year"},
                    {"name": f"{dt_col}_month", "type": "temporal", "source": dt_col, "component": "month"},
                    {"name": f"{dt_col}_dayofweek", "type": "temporal", "source": dt_col, "component": "dayofweek"},
                ])

            # 3. Categorical frequency encodings
            for cat_col in cat_cols[:3]:
                candidate_extractions.append({
                    "name": f"{cat_col}_freq",
                    "type": "frequency_encoding",
                    "source": cat_col,
                    "rationale": "Maps categories to prevalence in dataset; handles rare categories gracefully.",
                })

            extraction_payload = {
                "candidate_features_count": len(candidate_extractions),
                "proposed_extractions": candidate_extractions[:10],
                "pca_derived_features_available": state.get("pca_results", {}).get("is_appropriate", False),
            }

            state["feature_extraction_results"] = extraction_payload
            state.setdefault("completed_steps", []).append("feature_extraction")
            logger.info(f"[{self.name}] Proposed {len(candidate_extractions)} domain feature candidates.")
        except Exception as exc:
            logger.error(f"[{self.name}] Feature extraction error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
