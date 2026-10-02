"""
DataWise AI — Evaluation: Error Analysis
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd


def perform_error_analysis(
    y_true: Any,
    y_pred: Any,
    task_type: str = "classification",
    top_n: int = 10,
) -> Dict[str, Any]:
    """Analyzes worst model errors for diagnostic insights."""
    y_t = np.array(y_true)
    y_p = np.array(y_pred)

    if task_type.lower() == "classification":
        mismatches = np.where(y_t != y_p)[0]
        error_rate = len(mismatches) / max(len(y_t), 1)

        # Most frequent confusion pairs
        pairs: Dict[str, int] = {}
        for idx in mismatches:
            pair = f"True: {y_t[idx]} -> Pred: {y_p[idx]}"
            pairs[pair] = pairs.get(pair, 0) + 1

        top_confusions = sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "task_type": "classification",
            "total_errors": len(mismatches),
            "error_rate": round(error_rate, 4),
            "top_confusion_pairs": [{"pair": k, "count": v} for k, v in top_confusions],
        }
    else:
        abs_errors = np.abs(y_t - y_p)
        worst_indices = np.argsort(abs_errors)[::-1][:top_n]

        worst_cases = [
            {
                "index": int(i),
                "true_value": round(float(y_t[i]), 4),
                "predicted_value": round(float(y_p[i]), 4),
                "absolute_error": round(float(abs_errors[i]), 4),
            }
            for i in worst_indices
        ]

        return {
            "task_type": "regression",
            "mean_absolute_error": round(float(np.mean(abs_errors)), 4),
            "worst_predictions": worst_cases,
        }
