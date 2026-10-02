"""
DataWise AI — Visualization Tools Package
"""

from .distributions import generate_distribution_spec
from .categorical import generate_categorical_spec
from .correlation import generate_correlation_matrix_spec
from .outliers import generate_outlier_plot_spec
from .relationships import generate_scatter_spec
from .time_series import generate_time_series_spec
from .ml_evaluation import (
    generate_confusion_matrix_spec,
    generate_roc_curve_spec,
    generate_residuals_spec,
)

__all__ = [
    "generate_distribution_spec",
    "generate_categorical_spec",
    "generate_correlation_matrix_spec",
    "generate_outlier_plot_spec",
    "generate_scatter_spec",
    "generate_time_series_spec",
    "generate_confusion_matrix_spec",
    "generate_roc_curve_spec",
    "generate_residuals_spec",
]
