"""
DataWise AI — Evaluation Tools Package
"""

from .classification import evaluate_classification
from .regression import evaluate_regression
from .clustering import evaluate_clustering
from .cross_validation import run_cross_validation
from .learning_curves import generate_learning_curve_data
from .error_analysis import perform_error_analysis
from .overfitting_analyzer import OverfittingAnalyzer

__all__ = [
    "evaluate_classification",
    "evaluate_regression",
    "evaluate_clustering",
    "run_cross_validation",
    "generate_learning_curve_data",
    "perform_error_analysis",
    "OverfittingAnalyzer",
]
