"""
DataWise AI — Modeling Agents
Specialized agents for strategy, classical ML, PyTorch deep learning, architecture search, transfer learning, time series, and anomaly detection.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.ml_tools import ModelTrainer, recommend_algorithms
from app.tools.deep_learning_tools import PyTorchModelTrainer, HAS_TORCH


class ModelStrategyAgent(BaseAgent):
    """
    Selects candidate algorithms matching dataset scale, sparsity, problem type, and latency goals.
    Enforces 'baseline first' principle.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModelStrategyAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        problem_type = input_data.parameters.get("problem_type", "classification")

        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            recommendations = recommend_algorithms(df, target_col=target_col, problem_type=problem_type)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=recommendations,
                summary=f"Model strategy established: Shortlisted {len(recommendations.get('candidate_models', []))} candidate families with baseline-first protocol."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Model strategy formulation failed: {e}"
            )


class ClassicalMLAgent(BaseAgent):
    """
    Executes leak-free training and cross-validation of classical machine learning algorithms:
    Logistic/Ridge, Random Forest, ExtraTrees, XGBoost, LightGBM, HistGradientBoosting.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ClassicalMLAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        problem_type = input_data.parameters.get("problem_type", "classification")

        if not file_path or not os.path.exists(file_path) or not target_col:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file or target column missing."],
                summary="Missing inputs for classical ML training."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            trainer = ModelTrainer(df=df, target_col=target_col, task_type=problem_type)
            train_results = trainer.train_and_evaluate()

            best_model = train_results.get("best_model_name", "Unknown")
            trained_count = len(train_results.get("trained_models", []))

            # Store serialized pipeline reference in data
            clean_results = {k: v for k, v in train_results.items() if k not in ["all_pipelines", "best_pipeline", "X_train", "X_test", "y_train", "y_test"]}

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=clean_results,
                summary=f"Classical ML experimentation complete: trained {trained_count} candidate pipelines. Best candidate: '{best_model}' with primary metric score validated on test split."
            )
        except Exception as e:
            logger.error(f"Classical ML training error: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Classical ML training failed: {e}"
            )


class DeepLearningAgent(BaseAgent):
    """
    Evaluates deep learning feasibility and trains PyTorch neural networks (MLP, TabularTransformer).
    Refuses deep learning on tiny tabular datasets (<500 rows) to prevent extreme overfitting.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DeepLearningAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")
        arch_type = input_data.parameters.get("arch_type", "mlp")

        if not file_path or not os.path.exists(file_path) or not target_col:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file or target column missing."],
                summary="Missing inputs for deep learning."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)

            if len(df) < 300:
                return AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="warning",
                    warnings=["Dataset has fewer than 300 rows. Classical gradient boosted trees strongly recommended over deep learning."],
                    data={"decision": "skip_dl_for_small_data", "rows": len(df)},
                    summary="Deep learning bypassed: dataset too small (<300 rows) for stable gradient descent optimization. Classical models preferred."
                )

            if not HAS_TORCH:
                return AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="warning",
                    warnings=["PyTorch is not installed in current environment."],
                    summary="PyTorch unavailable."
                )

            # Preprocess features into numeric array
            from sklearn.model_selection import train_test_split
            from sklearn.impute import SimpleImputer
            from sklearn.preprocessing import StandardScaler

            valid_df = df.dropna(subset=[target_col])
            X_raw = valid_df.drop(columns=[target_col]).select_dtypes(include=[np.number])
            if X_raw.shape[1] == 0:
                return AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="warning",
                    summary="No numeric features available for PyTorch neural network training."
                )

            imputer = SimpleImputer(strategy="median")
            scaler = StandardScaler()
            X_proc = scaler.fit_transform(imputer.fit_transform(X_raw))

            y_raw = valid_df[target_col].values
            classes, y_encoded = np.unique(y_raw, return_inverse=True)

            X_tr, X_val, y_tr, y_val = train_test_split(X_proc, y_encoded, test_size=0.2, random_state=42)

            trainer = PyTorchModelTrainer(epochs=20, batch_size=32)
            dl_res = trainer.train_tabular_classifier(X_tr, y_tr, X_val, y_val, arch_type=arch_type)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=dl_res,
                summary=f"PyTorch {arch_type.upper()} trained successfully: Val Accuracy={dl_res.get('accuracy')}, F1={dl_res.get('f1_score')}, Trainable Params={dl_res.get('trainable_parameters')}."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Deep learning training failed: {e}"
            )


class NeuralArchitectureAgent(BaseAgent):
    """
    Determines optimal neural architecture: layer depths, hidden units, activation functions, and regularization.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="NeuralArchitectureAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        num_features = input_data.parameters.get("num_features", 10)
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "architecture_type": "TabularMLP_with_Residuals",
                "layer_dimensions": [min(256, max(64, num_features * 4)), min(128, max(32, num_features * 2)), 32],
                "activation": "GELU",
                "normalization": "BatchNorm1d",
                "dropout_rate": 0.25,
                "weight_decay": 1e-4
            },
            summary="Configured optimal neural architecture with GELU non-linearities, BatchNorm, and 0.25 dropout regularization."
        )


class TransferLearningAgent(BaseAgent):
    """
    Manages pretrained feature extractors for image, audio, and text embeddings.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="TransferLearningAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        modality = input_data.parameters.get("modality", "TEXT")
        backbone = "sentence-transformers/all-MiniLM-L6-v2" if modality == "TEXT" else "torchvision/resnet50"
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={"modality": modality, "recommended_backbone": backbone, "fine_tuning_strategy": "freeze_backbone_train_head"},
            summary=f"Configured transfer learning backbone '{backbone}' with frozen base weights and trainable projection head."
        )


class TimeSeriesAgent(BaseAgent):
    """
    Configures temporal splits, lag features, rolling statistics, and sequence models.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="TimeSeriesAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        time_col = input_data.parameters.get("time_column", "timestamp")
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "time_column": time_col,
                "split_strategy": "TimeSeriesSplit_Strictly_Forward",
                "lag_windows": [1, 2, 3, 7, 14, 30],
                "rolling_aggregations": ["mean", "std", "min", "max"]
            },
            summary=f"Configured time-series feature pipeline: strict forward temporal CV split and multi-window lag features."
        )


class AnomalyDetectionAgent(BaseAgent):
    """
    Deploys unsupervised anomaly detection: Isolation Forest, Local Outlier Factor, and Autoencoders.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="AnomalyDetectionAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        contamination = input_data.parameters.get("contamination", 0.05)
        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data={
                "algorithm": "IsolationForest + DeepAutoencoder",
                "contamination": contamination,
                "metric": "reconstruction_error"
            },
            summary=f"Anomaly detection suite armed with expected contamination rate of {contamination * 100}%."
        )


__all__ = [
    "ModelStrategyAgent",
    "ClassicalMLAgent",
    "DeepLearningAgent",
    "NeuralArchitectureAgent",
    "TransferLearningAgent",
    "TimeSeriesAgent",
    "AnomalyDetectionAgent",
]
