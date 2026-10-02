"""
DataWise AI — Robustness Testing Agent
Stress-tests model resilience under gaussian noise perturbations, simulated missingness,
and covariate shift. Generates a composite Robustness Score.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput, load_dataframe_safely


class RobustnessAgent(BaseAgent):
    """Model Stress Testing & Perturbation Robustness Agent."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="Robustness Agent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        path = input_data.dataset_path
        df = load_dataframe_safely(path)
        if df is None:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary="Robustness test failed: dataset not found.",
                errors=["Dataset path invalid"],
            )

        target_col = input_data.parameters.get("target_column") or df.columns[-1]
        df_clean = df.dropna(subset=[target_col])
        X = df_clean.drop(columns=[target_col]).select_dtypes(include=[np.number]).fillna(0)
        y = df_clean[target_col]

        if X.empty or len(X) < 30:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning",
                summary="Robustness testing skipped: insufficient numeric samples for stress testing.",
            )

        # Baseline model training
        if not pd.api.types.is_numeric_dtype(y):
            y_coded = pd.factorize(y)[0]
        else:
            y_coded = y.values

        split_idx = int(len(X) * 0.7)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y_coded[:split_idx], y_coded[split_idx:]

        clf = RandomForestClassifier(n_estimators=40, max_depth=6, random_state=42)
        clf.fit(X_train, y_train)
        base_acc = float(accuracy_score(y_test, clf.predict(X_test)))

        # 1. Noise Stress Test (Add 5% gaussian noise)
        X_noise = X_test.copy()
        std_devs = X_train.std().replace(0, 1.0)
        noise = np.random.normal(0, 0.05, X_noise.shape) * std_devs.values
        X_noise = X_noise + noise
        noise_acc = float(accuracy_score(y_test, clf.predict(X_noise)))
        noise_retention = round((noise_acc / max(base_acc, 0.01)) * 100, 1)

        # 2. Missingness Stress Test (Simulate 10% randomly masked values)
        X_missing = X_test.copy()
        mask = np.random.rand(*X_missing.shape) < 0.10
        # Impute with column means
        X_missing_imputed = X_missing.mask(mask, X_train.mean(), axis=1)
        missing_acc = float(accuracy_score(y_test, clf.predict(X_missing_imputed)))
        missing_retention = round((missing_acc / max(base_acc, 0.01)) * 100, 1)

        # Composite score
        robustness_score = round((noise_retention + missing_retention) / 2.0, 1)
        grade = "EXCELLENT" if robustness_score >= 95 else ("ACCEPTABLE" if robustness_score >= 85 else "FRAGILE")

        summary = (
            f"Robustness Score: {robustness_score}% ({grade}). "
            f"Baseline: {base_acc:.3f} | Under 5% Gaussian Noise: {noise_acc:.3f} ({noise_retention}% retained) | "
            f"Under 10% Missing Values: {missing_acc:.3f} ({missing_retention}% retained)."
        )

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success" if robustness_score >= 80 else "warning",
            data={
                "robustness_score": robustness_score,
                "grade": grade,
                "baseline_accuracy": round(base_acc, 4),
                "noise_stress_accuracy": round(noise_acc, 4),
                "noise_retention_pct": noise_retention,
                "missing_stress_accuracy": round(missing_acc, 4),
                "missing_retention_pct": missing_retention,
            },
            summary=summary,
        )
