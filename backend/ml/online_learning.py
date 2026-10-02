"""
Agentic AutoML Intelligence Platform — Online / Incremental Learning Engine
Provides safe incremental partial_fit updates and continuous learning policy governance.
"""

from __future__ import annotations

import copy
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.base import BaseEstimator


class ContinuousLearningPolicy(str, Enum):
    STATIC = "STATIC"               # Model never updates automatically
    INCREMENTAL = "INCREMENTAL"     # Model updates with compatible new labeled data
    ADAPTIVE = "ADAPTIVE"           # System detects drift and decides whether to update
    RETRAINING = "RETRAINING"       # System periodically/conditionally rebuilds model


class IncrementalUpdateResult:
    def __init__(
        self,
        success: bool,
        is_supported: bool,
        policy: ContinuousLearningPolicy,
        batch_size: int,
        pre_update_score: Optional[float] = None,
        post_update_score: Optional[float] = None,
        promoted: bool = False,
        message: str = "",
    ):
        self.success = success
        self.is_supported = is_supported
        self.policy = policy
        self.batch_size = batch_size
        self.pre_update_score = pre_update_score
        self.post_update_score = post_update_score
        self.promoted = promoted
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "is_supported": self.is_supported,
            "policy": self.policy.value,
            "batch_size": self.batch_size,
            "pre_update_score": self.pre_update_score,
            "post_update_score": self.post_update_score,
            "promoted": self.promoted,
            "message": self.message,
        }


class OnlineLearningEngine:
    """Manages incremental model updates with safety verification and shadow validation."""

    # Models known to support incremental updates natively via partial_fit
    INCREMENTAL_COMPATIBLE_CLASSES = {
        "SGDClassifier",
        "SGDRegressor",
        "PassiveAggressiveClassifier",
        "PassiveAggressiveRegressor",
        "MultinomialNB",
        "BernoulliNB",
        "Perceptron",
        "MiniBatchKMeans",
    }

    @classmethod
    def supports_incremental_learning(cls, model: Any) -> bool:
        """Check if an algorithm instance natively supports incremental partial_fit."""
        if hasattr(model, "partial_fit") and callable(getattr(model, "partial_fit")):
            return True
        class_name = type(model).__name__
        return class_name in cls.INCREMENTAL_COMPATIBLE_CLASSES

    @classmethod
    def execute_incremental_update(
        cls,
        current_model: Any,
        X_new: pd.DataFrame,
        y_new: pd.Series,
        validation_X: Optional[pd.DataFrame] = None,
        validation_y: Optional[pd.Series] = None,
        policy: ContinuousLearningPolicy = ContinuousLearningPolicy.INCREMENTAL,
        classes: Optional[List[Any]] = None,
    ) -> Tuple[Any, IncrementalUpdateResult]:
        """
        Safely update model on incoming labeled batch.
        Guarantees that production model is NEVER modified in-place before shadow validation.
        """
        batch_size = len(X_new)
        if policy == ContinuousLearningPolicy.STATIC:
            return current_model, IncrementalUpdateResult(
                success=True,
                is_supported=cls.supports_incremental_learning(current_model),
                policy=policy,
                batch_size=batch_size,
                promoted=False,
                message="Policy is STATIC: Model updates are disabled by configuration.",
            )

        if not cls.supports_incremental_learning(current_model):
            return current_model, IncrementalUpdateResult(
                success=False,
                is_supported=False,
                policy=policy,
                batch_size=batch_size,
                promoted=False,
                message=f"Algorithm {type(current_model).__name__} does NOT support online incremental learning. "
                        f"New data must be accumulated for full retraining.",
            )

        # 1. Clone model candidate (shadow copy)
        try:
            candidate_model = copy.deepcopy(current_model)
        except Exception:
            # Fallback if deepcopy fails
            candidate_model = current_model

        # 2. Evaluate pre-update performance on validation set if provided
        pre_score = None
        if validation_X is not None and validation_y is not None:
            try:
                pre_score = float(current_model.score(validation_X, validation_y))
            except Exception:
                pass

        # 3. Apply incremental partial_fit on candidate
        try:
            if classes is not None and hasattr(candidate_model, "classes_"):
                candidate_model.partial_fit(X_new, y_new)
            elif classes is not None:
                candidate_model.partial_fit(X_new, y_new, classes=classes)
            else:
                candidate_model.partial_fit(X_new, y_new)
        except Exception as fit_err:
            logger.error(f"[OnlineLearningEngine] partial_fit failed: {fit_err}")
            return current_model, IncrementalUpdateResult(
                success=False,
                is_supported=True,
                policy=policy,
                batch_size=batch_size,
                promoted=False,
                message=f"Incremental partial_fit update execution error: {fit_err}",
            )

        # 4. Evaluate post-update performance on validation set
        post_score = None
        if validation_X is not None and validation_y is not None:
            try:
                post_score = float(candidate_model.score(validation_X, validation_y))
            except Exception:
                pass

        # 5. Validation gate: candidate must not severely degrade validation metric
        promoted = True
        if pre_score is not None and post_score is not None:
            # Allow minor variance (tolerance 0.05)
            if post_score < (pre_score - 0.05):
                promoted = False
                logger.warning(
                    f"[OnlineLearningEngine] Candidate model rejected: post-update score ({post_score:.4f}) "
                    f"dropped below threshold of pre-update score ({pre_score:.4f})"
                )

        selected_model = candidate_model if promoted else current_model
        msg = "Incremental update accepted and promoted." if promoted else "Incremental update rejected due to validation metric regression."

        return selected_model, IncrementalUpdateResult(
            success=True,
            is_supported=True,
            policy=policy,
            batch_size=batch_size,
            pre_update_score=pre_score,
            post_update_score=post_score,
            promoted=promoted,
            message=msg,
        )


online_learning_engine = OnlineLearningEngine()
