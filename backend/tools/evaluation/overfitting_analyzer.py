"""
DataWise AI — Overfitting and Underfitting Diagnosis Tool
Analyzes train score, cross-validation score, and hold-out test score gaps.
Detects high variance, high bias, and poor generalization.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class GeneralizationDiagnosis(BaseModel):
    train_score: float
    cv_score_mean: float
    cv_score_std: float
    test_score: float
    train_test_gap: float
    cv_test_gap: float
    status: str            # "Good Generalization", "Mild Overfitting", "Severe Overfitting", "Underfitting", "Data Leakage Suspected"
    severity: str          # "LOW", "MEDIUM", "HIGH"
    diagnosis_reason: str
    recommendation: str


class OverfittingAnalyzer:
    """Diagnoses model generalization health across train, CV, and test splits."""

    @staticmethod
    def analyze(
        train_score: float,
        cv_score_mean: float,
        cv_score_std: float,
        test_score: float,
        primary_metric: str = "ROC-AUC",
        higher_is_better: bool = True,
    ) -> GeneralizationDiagnosis:
        if higher_is_better:
            train_test_gap = train_score - test_score
            cv_test_gap = cv_score_mean - test_score
        else:
            train_test_gap = test_score - train_score
            cv_test_gap = test_score - cv_score_mean

        train_test_gap = round(float(train_test_gap), 4)
        cv_test_gap = round(float(cv_test_gap), 4)

        # 1. Check for underfitting (both train and test are low)
        if higher_is_better and train_score < 0.60:
            status = "Underfitting"
            severity = "HIGH"
            reason = (
                f"Training score ({train_score:.2f}) is low under {primary_metric}, indicating high bias. "
                "The model is not capturing the underlying feature relationships."
            )
            rec = "Consider increasing model complexity, adding engineered interaction features, or relaxing regularization."

        # 2. Check for severe overfitting (large train-test gap > 0.15)
        elif train_test_gap > 0.15:
            status = "Severe Overfitting"
            severity = "HIGH"
            reason = (
                f"Large gap of {train_test_gap * 100:.1f}% between training score ({train_score:.2f}) "
                f"and test score ({test_score:.2f}). Model has memorized training noise."
            )
            rec = "Increase regularization (higher alpha/lower C), reduce tree max_depth, use more cross-validation folds, or gather more training samples."

        # 3. Check for mild overfitting (gap between 0.05 and 0.15)
        elif train_test_gap > 0.05:
            status = "Mild Overfitting"
            severity = "MEDIUM"
            reason = (
                f"Moderate gap of {train_test_gap * 100:.1f}% between train ({train_score:.2f}) and test ({test_score:.2f}). "
                "Acceptable for many complex domains, but regularization could improve test stability."
            )
            rec = "Tune hyperparameters with tighter constraints (e.g. min_samples_leaf) or perform feature selection to remove noisy predictors."

        # 4. Check for potential test leakage or anomaly (test noticeably higher than train)
        elif train_test_gap < -0.10:
            status = "Data Leakage Suspected"
            severity = "HIGH"
            reason = (
                f"Test score ({test_score:.2f}) is substantially higher than training score ({train_score:.2f}). "
                "Check for holdout data leakage or unrepresentative test partition."
            )
            rec = "Inspect split stratification and ensure feature transformations were fitted strictly on the training partition."

        # 5. Good Generalization
        else:
            status = "Good Generalization"
            severity = "LOW"
            reason = (
                f"Model exhibits balanced generalization with train ({train_score:.2f}), CV ({cv_score_mean:.2f}), "
                f"and test ({test_score:.2f}) scores closely aligned (gap: {train_test_gap * 100:.1f}%)."
            )
            rec = "Model is well-calibrated and ready for deployment consideration."

        return GeneralizationDiagnosis(
            train_score=round(float(train_score), 4),
            cv_score_mean=round(float(cv_score_mean), 4),
            cv_score_std=round(float(cv_score_std), 4),
            test_score=round(float(test_score), 4),
            train_test_gap=train_test_gap,
            cv_test_gap=cv_test_gap,
            status=status,
            severity=severity,
            diagnosis_reason=reason,
            recommendation=rec,
        )
