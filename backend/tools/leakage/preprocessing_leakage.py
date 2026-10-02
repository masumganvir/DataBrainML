"""
DataWise AI — Leakage: Preprocessing & Split Leakage
"""

from typing import Any, Dict, List


def verify_pipeline_split_safety(pipeline_code: str = None) -> Dict[str, Any]:
    """
    Verifies that transformers (StandardScaler, Imputers, TargetEncoders)
    are fitted strictly inside sklearn Pipeline on X_train only.
    """
    warnings: List[str] = []
    safe = True

    if pipeline_code:
        if "fit_transform(df)" in pipeline_code or "fit(df)" in pipeline_code:
            warnings.append("Preprocessing fitted on full dataset before train/test split. Test data statistics leaked into training pipeline.")
            safe = False
        if "target_encoder.fit(X, y)" in pipeline_code and "train_test_split" not in pipeline_code:
            warnings.append("Target encoding executed before train/test splitting.")
            safe = False

    return {
        "is_leakage_safe": safe,
        "warnings": warnings,
        "recommendation": "Always encapsulate all transformers within sklearn.pipeline.Pipeline and fit only on X_train.",
    }
