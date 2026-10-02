"""
Validation Manager
Independently verifies and validates recovered artifacts, pipelines, schemas,
and models before permitting any workflow to resume.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field


class ValidationReport(BaseModel):
    """Result of independent post-recovery validation check."""
    is_valid: bool
    stage: str
    checks_passed: List[str] = Field(default_factory=list)
    checks_failed: List[str] = Field(default_factory=list)
    validation_message: str = ""
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ValidationManager:
    """Independent verification gate ensuring recovered objects meet functional standards."""

    @classmethod
    def validate_data_schema(
        cls, df: Optional[pd.DataFrame], expected_columns: Optional[List[str]] = None
    ) -> ValidationReport:
        """Validates that a recovered DataFrame is non-empty and matches schema expectations."""
        if df is None:
            return ValidationReport(
                is_valid=False,
                stage="data_validation",
                checks_failed=["DataFrame is None"],
                validation_message="Recovered data object is null.",
            )

        checks_passed = []
        checks_failed = []

        if len(df) > 0:
            checks_passed.append(f"Row count > 0 (n={len(df)})")
        else:
            checks_failed.append("DataFrame has 0 rows")

        if len(df.columns) > 0:
            checks_passed.append(f"Column count > 0 (n={len(df.columns)})")
        else:
            checks_failed.append("DataFrame has 0 columns")

        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            if not missing:
                checks_passed.append("All expected columns present")
            else:
                checks_failed.append(f"Missing expected columns: {list(missing)[:5]}")

        is_valid = len(checks_failed) == 0
        return ValidationReport(
            is_valid=is_valid,
            stage="data_validation",
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            validation_message="Data validation succeeded." if is_valid else "Data validation failed.",
            metrics={"rows": len(df), "columns": len(df.columns)},
        )

    @classmethod
    def validate_preprocessing_pipeline(
        cls, pipeline: Any, sample_df: pd.DataFrame
    ) -> ValidationReport:
        """Runs a live test transformation on sample data to confirm pipeline stability."""
        if pipeline is None:
            return ValidationReport(
                is_valid=False,
                stage="preprocessing_validation",
                checks_failed=["Pipeline object is None"],
                validation_message="Preprocessing pipeline is null.",
            )

        checks_passed = []
        checks_failed = []

        try:
            # Test transform
            if hasattr(pipeline, "fit_transform"):
                try:
                    out = pipeline.transform(sample_df.head(5))
                except Exception:
                    out = pipeline.fit_transform(sample_df.head(5))
                checks_passed.append("pipeline transformation succeeded on sample batch")
            elif hasattr(pipeline, "transform"):
                out = pipeline.transform(sample_df.head(5))
                checks_passed.append("pipeline.transform() succeeded on sample batch")
            else:
                checks_failed.append("Pipeline missing standard transform methods")
                return ValidationReport(
                    is_valid=False,
                    stage="preprocessing_validation",
                    checks_failed=checks_failed,
                    validation_message="Object lacks scikit-learn compatible transformation interface.",
                )

            # Check for NaN generation in transformed output
            if isinstance(out, (np.ndarray, pd.DataFrame)):
                if np.isnan(out).any() if isinstance(out, np.ndarray) else out.isna().any().any():
                    checks_failed.append("Transformed output contains unexpected NaN values")
                else:
                    checks_passed.append("Transformed output is non-null")

            is_valid = len(checks_failed) == 0
            return ValidationReport(
                is_valid=is_valid,
                stage="preprocessing_validation",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                validation_message="Preprocessing pipeline verified." if is_valid else "Preprocessing verification failed.",
            )
        except Exception as exc:
            return ValidationReport(
                is_valid=False,
                stage="preprocessing_validation",
                checks_failed=[f"Execution exception: {str(exc)}"],
                validation_message=f"Pipeline transformation validation error: {str(exc)}",
            )

    @classmethod
    def validate_model_inference(
        cls, model: Any, sample_features: Union[pd.DataFrame, np.ndarray]
    ) -> ValidationReport:
        """Executes a test prediction to verify that a recovered model is functional."""
        if model is None:
            return ValidationReport(
                is_valid=False,
                stage="model_validation",
                checks_failed=["Model object is None"],
                validation_message="Model object is null.",
            )

        checks_passed = []
        checks_failed = []

        try:
            if not hasattr(model, "predict"):
                checks_failed.append("Model lacks predict() method")
                return ValidationReport(
                    is_valid=False,
                    stage="model_validation",
                    checks_failed=checks_failed,
                    validation_message="Object lacks predict interface.",
                )

            preds = model.predict(sample_features)
            checks_passed.append(f"model.predict() succeeded with {len(preds)} predictions")

            if len(preds) == 0:
                checks_failed.append("Model returned empty prediction array")
            elif np.isnan(preds).any() if isinstance(preds, np.ndarray) else False:
                checks_failed.append("Model predictions contain NaN values")
            else:
                checks_passed.append("Predictions are well-formed and non-null")

            is_valid = len(checks_failed) == 0
            return ValidationReport(
                is_valid=is_valid,
                stage="model_validation",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                validation_message="Model inference validated successfully." if is_valid else "Model prediction check failed.",
                metrics={"sample_size": len(preds)},
            )
        except Exception as exc:
            return ValidationReport(
                is_valid=False,
                stage="model_validation",
                checks_failed=[f"Inference exception: {str(exc)}"],
                validation_message=f"Model validation check failed: {str(exc)}",
            )

    @classmethod
    def validate_deployment_health(
        cls, health_check_callable: Callable[[], bool]
    ) -> ValidationReport:
        """Executes health probe on deployed service endpoint."""
        try:
            healthy = health_check_callable()
            return ValidationReport(
                is_valid=bool(healthy),
                stage="deployment_validation",
                checks_passed=["Health endpoint check returned True"] if healthy else [],
                checks_failed=[] if healthy else ["Health probe returned non-200 / False"],
                validation_message="Deployment health check passed." if healthy else "Deployment health check failed.",
            )
        except Exception as exc:
            return ValidationReport(
                is_valid=False,
                stage="deployment_validation",
                checks_failed=[f"Health probe exception: {str(exc)}"],
                validation_message=f"Deployment probe failed: {str(exc)}",
            )
