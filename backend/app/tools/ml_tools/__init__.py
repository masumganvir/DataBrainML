"""
DataWise AI — Machine Learning Tools
Deterministic model training, baseline establishment, algorithm selection, and validation.
"""

from __future__ import annotations

from app.tools.model_trainer import (
    ModelTrainer,
    train_candidate_models,
)
from app.tools.ml_recommender import (
    recommend_algorithms,
    get_algorithm_suitability,
)
from app.tools.target_detector import (
    detect_target_column,
    classify_problem_type,
)

__all__ = [
    "ModelTrainer",
    "train_candidate_models",
    "recommend_algorithms",
    "get_algorithm_suitability",
    "detect_target_column",
    "classify_problem_type",
]
