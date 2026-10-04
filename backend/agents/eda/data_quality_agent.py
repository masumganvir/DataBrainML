"""
DataWise AI — Data Quality Agent
Section 7 Specification:
Audits missing percentage, duplicate percentage, invalid/infinite values, constant columns,
near-zero variance, incorrect/mixed types, potential leakage, ID columns, and high-cardinality features.
Produces data_quality_report.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
import numpy as np
import pandas as pd

from backend.agents.eda.eda_state import EDAState


class DataQualityAgent:
    """Evaluates data integrity, health scores, and potential data risks."""

    def __init__(self, name: str = "DataQualityAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        """Runs thorough data health diagnostics and writes data_quality_report.json."""
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path or not Path(dataset_path).exists():
                    raise FileNotFoundError(f"Dataset path not found: {dataset_path}")
                df = pd.read_csv(dataset_path)

            n_rows, n_cols = df.shape
            profile = state.get("dataset_profile", {})

            # 1. Missing values audit
            missing_per_col = df.isnull().sum()
            total_missing = int(missing_per_col.sum())
            missing_pct = round((total_missing / max(1, n_rows * n_cols)) * 100, 2)
            cols_with_missing = {
                col: {"count": int(cnt), "pct": round((int(cnt) / max(1, n_rows)) * 100, 2)}
                for col, cnt in missing_per_col.items() if cnt > 0
            }

            # 2. Duplicate audit
            duplicates_count = int(df.duplicated().sum())
            duplicates_pct = round((duplicates_count / max(1, n_rows)) * 100, 2)

            # 3. Infinite values in numerical columns
            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            infinite_records: Dict[str, int] = {}
            near_zero_variance_cols: List[str] = []

            for col in num_cols:
                series = df[col]
                inf_count = int(np.isinf(series).sum())
                if inf_count > 0:
                    infinite_records[col] = inf_count

                # Variance check
                var = float(series.var()) if series.dropna().shape[0] > 1 else 0.0
                if var < 1e-4:
                    near_zero_variance_cols.append(col)

            # 4. Mixed types in object columns
            mixed_type_cols: List[str] = []
            for col in df.select_dtypes(include=["object"]).columns:
                inferred = set(df[col].dropna().apply(lambda x: type(x).__name__))
                if len(inferred) > 1:
                    mixed_type_cols.append(col)

            # 5. Potential Leakage (columns with near-perfect correlation with target or suspicious names)
            target_col = state.get("target_column")
            leakage_candidates: List[Dict[str, Any]] = []
            if target_col and target_col in df.columns:
                target_series = df[target_col]
                for col in num_cols:
                    if col == target_col:
                        continue
                    try:
                        valid = df[[col, target_col]].dropna()
                        if len(valid) > 10:
                            corr = abs(float(valid[col].corr(valid[target_col])))
                            if corr > 0.98:
                                leakage_candidates.append({
                                    "column": col,
                                    "correlation_with_target": round(corr, 4),
                                    "reason": "Extreme correlation with target (>0.98); potential post-event feature or target proxy.",
                                })
                    except Exception:
                        pass

            # 6. Overall Quality Score computation (0 to 100)
            deductions = 0.0
            if missing_pct > 0:
                deductions += min(25.0, missing_pct * 1.5)
            if duplicates_pct > 0:
                deductions += min(15.0, duplicates_pct * 2.0)
            if infinite_records:
                deductions += 10.0
            if near_zero_variance_cols:
                deductions += min(10.0, len(near_zero_variance_cols) * 2.5)
            if leakage_candidates:
                deductions += 20.0

            quality_score = max(20.0, round(100.0 - deductions, 1))

            health_status = "Excellent"
            if quality_score < 60:
                health_status = "Poor"
            elif quality_score < 75:
                health_status = "Fair"
            elif quality_score < 90:
                health_status = "Good"

            quality_payload = {
                "quality_score": quality_score,
                "health_status": health_status,
                "total_rows": n_rows,
                "total_columns": n_cols,
                "missing_total": total_missing,
                "missing_percentage": missing_pct,
                "columns_with_missing": cols_with_missing,
                "duplicate_rows": duplicates_count,
                "duplicate_percentage": duplicates_pct,
                "infinite_values": infinite_records,
                "near_zero_variance_columns": near_zero_variance_cols,
                "mixed_type_columns": mixed_type_cols,
                "potential_leakage_features": leakage_candidates,
                "id_columns": profile.get("id_columns", []),
                "high_cardinality_columns": profile.get("high_cardinality_columns", []),
                "constant_columns": profile.get("constant_columns", []),
            }

            state["data_quality_report"] = quality_payload
            state["missing_summary"] = {
                "total_missing": total_missing,
                "missing_pct": missing_pct,
                "columns": cols_with_missing,
            }
            state.setdefault("completed_steps", []).append("data_quality")

            # Save data_quality_report.json
            output_dir = Path(state.get("output_dir", f"artifacts/{state.get('run_id', 'run_001')}/visualizations")).parent
            dq_path = output_dir / "data_quality_report.json"
            dq_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dq_path, "w", encoding="utf-8") as f:
                json.dump(quality_payload, f, indent=2)
            state.setdefault("artifacts", {})["data_quality_report"] = str(dq_path)

            logger.info(f"[{self.name}] Data Quality Score: {quality_score}/100 ({health_status}).")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in data quality analysis: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})
            state.setdefault("warnings", []).append(f"Quality audit completed with fallback: {exc}")

        return state
