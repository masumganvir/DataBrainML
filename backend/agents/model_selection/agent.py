"""
DataWise AI — Model Selection Agent
Selects candidate algorithms across linear, ensemble, kernel, and gradient boosting
families based on sample size, latency, interpretability, and problem type.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class ModelSelectionAgent(BaseAgent):
    """Algorithm Portfolio Selection Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Model Selection Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        params = input_data.parameters or {}
        problem_type = params.get("problem_type", "classification")
        n_samples = params.get("n_samples", 1000)
        n_features = params.get("n_features", 10)
        prefer_interpretable = params.get("prefer_interpretable", False)

        candidates: List[Dict[str, Any]] = []

        if problem_type == "classification":
            # 1. Baseline Interpretable Linear
            candidates.append({
                "model_name": "LogisticRegression",
                "family": "linear",
                "interpretability": "HIGH",
                "training_speed": "FAST",
                "rationale": "Fast calibrated baseline with direct odds ratio interpretability.",
            })
            # 2. Random Forest
            candidates.append({
                "model_name": "RandomForestClassifier",
                "family": "ensemble_bagging",
                "interpretability": "MEDIUM",
                "training_speed": "MEDIUM",
                "rationale": "Robust against overfitting, non-linear relationships, and outliers.",
            })
            # 3. Gradient Boosting
            candidates.append({
                "model_name": "GradientBoostingClassifier",
                "family": "ensemble_boosting",
                "interpretability": "MEDIUM",
                "training_speed": "MEDIUM",
                "rationale": "High competitive predictive power via sequential gradient optimization.",
            })
            # 4. Fast HistGradientBoosting for larger data
            if n_samples > 2000:
                candidates.append({
                    "model_name": "HistGradientBoostingClassifier",
                    "family": "histogram_boosting",
                    "interpretability": "MEDIUM",
                    "training_speed": "VERY_FAST",
                    "rationale": "Binning-based tree boosting optimized for scale and missing value handling.",
                })
            elif not prefer_interpretable:
                candidates.append({
                    "model_name": "ExtraTreesClassifier",
                    "family": "ensemble_randomized",
                    "interpretability": "MEDIUM",
                    "training_speed": "FAST",
                    "rationale": "Extremely randomized trees with lower variance than standard RF.",
                })

        elif problem_type == "regression":
            # 1. Ridge Baseline
            candidates.append({
                "model_name": "Ridge",
                "family": "linear_regularized",
                "interpretability": "HIGH",
                "training_speed": "VERY_FAST",
                "rationale": "L2 regularized linear model, optimal baseline immune to multicollinearity.",
            })
            # 2. Random Forest Regressor
            candidates.append({
                "model_name": "RandomForestRegressor",
                "family": "ensemble_bagging",
                "interpretability": "MEDIUM",
                "training_speed": "MEDIUM",
                "rationale": "Captures complex non-linear feature interactions without manual transformation.",
            })
            # 3. Gradient Boosting Regressor
            candidates.append({
                "model_name": "GradientBoostingRegressor",
                "family": "ensemble_boosting",
                "interpretability": "MEDIUM",
                "training_speed": "MEDIUM",
                "rationale": "Minimizes residual squared loss across sequential tree stages.",
            })

        elif problem_type == "clustering":
            candidates.extend([
                {
                    "model_name": "KMeans",
                    "family": "centroid_clustering",
                    "interpretability": "HIGH",
                    "training_speed": "VERY_FAST",
                    "rationale": "Efficient partitioning into k spherical clusters with Voronoi boundaries.",
                },
                {
                    "model_name": "DBSCAN",
                    "family": "density_clustering",
                    "interpretability": "MEDIUM",
                    "training_speed": "FAST",
                    "rationale": "Density-based clustering finding arbitrary shaped clusters and noise.",
                },
                {
                    "model_name": "GaussianMixture",
                    "family": "probabilistic_clustering",
                    "interpretability": "MEDIUM",
                    "training_speed": "MEDIUM",
                    "rationale": "Soft clustering with elliptical covariance distributions.",
                },
            ])

        elif problem_type == "anomaly_detection":
            candidates.extend([
                {
                    "model_name": "IsolationForest",
                    "family": "tree_isolation",
                    "interpretability": "HIGH",
                    "training_speed": "VERY_FAST",
                    "rationale": "Isolates anomalous instances near root nodes of random trees.",
                },
                {
                    "model_name": "LocalOutlierFactor",
                    "family": "density_neighbors",
                    "interpretability": "MEDIUM",
                    "training_speed": "FAST",
                    "rationale": "Compares local density against k-nearest neighbors to detect anomalies.",
                },
            ])

        summary = (
            f"Selected {len(candidates)} candidate algorithm(s) for {problem_type}: "
            f"{', '.join([c['model_name'] for c in candidates])}."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "candidate_models": candidates,
                "problem_type": problem_type,
                "total_candidates": len(candidates),
            },
            summary=summary,
        )
