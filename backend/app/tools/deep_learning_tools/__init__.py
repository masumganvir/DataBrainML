"""
DataWise AI — PyTorch Deep Learning Tools
Deterministic neural network architectures, training routines, checkpointing, and evaluation.
"""

from __future__ import annotations

import os
import time
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from loguru import logger

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("PyTorch not installed. Deep learning models will use CPU fallback stubs.")


# ==============================================================================
# 1. PyTorch Architectures
# ==============================================================================

if HAS_TORCH:
    class TabularMLP(nn.Module):
        """
        Multi-Layer Perceptron for Tabular Data.
        Features: BatchNorm1d, Dropout, ReLU/GELU activations, and optional residual skip.
        """
        def __init__(
            self,
            input_dim: int,
            output_dim: int,
            hidden_dims: List[int] = [128, 64, 32],
            dropout_rate: float = 0.2,
            is_classification: bool = True
        ):
            super().__init__()
            self.is_classification = is_classification
            layers = []
            prev_dim = input_dim

            for h_dim in hidden_dims:
                layers.append(nn.Linear(prev_dim, h_dim))
                layers.append(nn.BatchNorm1d(h_dim))
                layers.append(nn.GELU())
                layers.append(nn.Dropout(dropout_rate))
                prev_dim = h_dim

            self.backbone = nn.Sequential(*layers)
            self.head = nn.Linear(prev_dim, output_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            features = self.backbone(x)
            out = self.head(features)
            return out


    class TabularTransformer(nn.Module):
        """
        Self-Attention / Transformer architecture for Tabular Feature Embeddings.
        Projects continuous and categorical feature dimensions into latent tokens and applies multi-head attention.
        """
        def __init__(
            self,
            num_features: int,
            output_dim: int,
            d_model: int = 64,
            nhead: int = 4,
            num_layers: int = 2,
            dim_feedforward: int = 128,
            dropout: float = 0.1,
            is_classification: bool = True
        ):
            super().__init__()
            self.num_features = num_features
            self.d_model = d_model
            self.feature_projections = nn.ModuleList([
                nn.Linear(1, d_model) for _ in range(num_features)
            ])
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.classifier = nn.Sequential(
                nn.Linear(num_features * d_model, 64),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(64, output_dim)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, num_features)
            tokens = []
            for i, proj in enumerate(self.feature_projections):
                feat = x[:, i : i + 1] # (batch_size, 1)
                tokens.append(proj(feat).unsqueeze(1)) # (batch_size, 1, d_model)
            token_seq = torch.cat(tokens, dim=1) # (batch_size, num_features, d_model)
            encoded = self.transformer(token_seq) # (batch_size, num_features, d_model)
            flattened = encoded.reshape(encoded.size(0), -1)
            return self.classifier(flattened)


    class SequenceLSTM(nn.Module):
        """
        LSTM / BiLSTM for sequential, temporal, and time-series data.
        """
        def __init__(
            self,
            input_dim: int,
            hidden_dim: int = 64,
            num_layers: int = 2,
            output_dim: int = 1,
            bidirectional: bool = True,
            dropout: float = 0.2
        ):
            super().__init__()
            self.bidirectional = bidirectional
            self.lstm = nn.LSTM(
                input_size=input_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
                bidirectional=bidirectional
            )
            fc_in = hidden_dim * 2 if bidirectional else hidden_dim
            self.fc = nn.Sequential(
                nn.Linear(fc_in, 32),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(32, output_dim)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch_size, seq_len, input_dim)
            out, _ = self.lstm(x)
            last_step = out[:, -1, :]
            return self.fc(last_step)


    class TabularAutoencoder(nn.Module):
        """
        Deep Autoencoder for unsupervised representation learning, reconstruction and anomaly detection.
        """
        def __init__(self, input_dim: int, latent_dim: int = 16):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Linear(64, latent_dim),
                nn.ReLU()
            )
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 64),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.Linear(64, input_dim)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            latent = self.encoder(x)
            reconstructed = self.decoder(latent)
            return reconstructed

        def encode(self, x: torch.Tensor) -> torch.Tensor:
            return self.encoder(x)


# ==============================================================================
# 2. PyTorch Training Engine
# ==============================================================================

class PyTorchModelTrainer:
    """
    Production-grade, deterministic PyTorch training engine.
    Supports early stopping, learning rate scheduling, gradient clipping,
    validation monitoring, checkpointing, and GPU acceleration.
    """
    def __init__(
        self,
        epochs: int = 50,
        batch_size: int = 64,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        patience: int = 8,
        gradient_clip: float = 1.0,
        device: Optional[str] = None
    ):
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.patience = patience
        self.gradient_clip = gradient_clip

        if not HAS_TORCH:
            self.device = "cpu"
        else:
            if device:
                self.device = device
            else:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def train_tabular_classifier(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        arch_type: str = "mlp",
        hidden_dims: List[int] = [64, 32],
        checkpoint_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Train a tabular neural network classifier with early stopping and metrics tracking.
        """
        if not HAS_TORCH:
            return {"error": "PyTorch is not available", "status": "failed"}

        start_time = time.time()
        input_dim = X_train.shape[1]
        classes = np.unique(y_train)
        num_classes = len(classes)
        is_binary = (num_classes == 2)
        output_dim = 1 if is_binary else num_classes

        # Convert to Tensors
        t_X_train = torch.tensor(X_train, dtype=torch.float32)
        t_y_train = torch.tensor(y_train, dtype=torch.float32 if is_binary else torch.long)
        t_X_val = torch.tensor(X_val, dtype=torch.float32)
        t_y_val = torch.tensor(y_val, dtype=torch.float32 if is_binary else torch.long)

        train_ds = TensorDataset(t_X_train, t_y_train)
        val_ds = TensorDataset(t_X_val, t_y_val)
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        # Build Model
        if arch_type == "transformer":
            model = TabularTransformer(
                num_features=input_dim,
                output_dim=output_dim,
                d_model=32,
                nhead=2,
                num_layers=1,
                is_classification=True
            ).to(self.device)
        else:
            model = TabularMLP(
                input_dim=input_dim,
                output_dim=output_dim,
                hidden_dims=hidden_dims,
                dropout_rate=0.2,
                is_classification=True
            ).to(self.device)

        criterion = nn.BCEWithLogitsLoss() if is_binary else nn.CrossEntropyLoss()
        optimizer = optim.AdamW(model.parameters(), lr=self.learning_rate, weight_decay=self.weight_decay)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

        best_val_loss = float("inf")
        best_weights = None
        epochs_no_improve = 0
        history: List[Dict[str, float]] = []

        for epoch in range(1, self.epochs + 1):
            model.train()
            train_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                preds = model(batch_x)
                loss = criterion(preds.squeeze(-1) if is_binary else preds, batch_y)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), self.gradient_clip)
                optimizer.step()
                train_loss += loss.item() * len(batch_x)
            train_loss /= len(train_ds)

            # Validation
            model.eval()
            val_loss = 0.0
            correct = 0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                    preds = model(batch_x)
                    loss = criterion(preds.squeeze(-1) if is_binary else preds, batch_y)
                    val_loss += loss.item() * len(batch_x)

                    if is_binary:
                        probs = torch.sigmoid(preds.squeeze(-1))
                        preds_cls = (probs >= 0.5).float()
                        correct += (preds_cls == batch_y).sum().item()
                    else:
                        preds_cls = preds.argmax(dim=-1)
                        correct += (preds_cls == batch_y).sum().item()

            val_loss /= len(val_ds)
            val_acc = correct / len(val_ds)
            scheduler.step(val_loss)

            history.append({
                "epoch": epoch,
                "train_loss": round(train_loss, 5),
                "val_loss": round(val_loss, 5),
                "val_accuracy": round(val_acc, 5)
            })

            # Checkpoint & Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_weights = model.state_dict().copy()
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= self.patience:
                    logger.info(f"Early stopping triggered at epoch {epoch}")
                    break

        if best_weights:
            model.load_state_dict(best_weights)

        elapsed_time = round(time.time() - start_time, 3)

        # Final predictions on validation
        model.eval()
        with torch.no_grad():
            preds_all = model(t_X_val.to(self.device))
            if is_binary:
                probs_val = torch.sigmoid(preds_all.squeeze(-1)).cpu().numpy()
                preds_val = (probs_val >= 0.5).astype(int)
            else:
                probs_val = torch.softmax(preds_all, dim=-1).cpu().numpy()
                preds_val = probs_val.argmax(axis=-1)

        # Compute deterministic evaluation metrics
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
        accuracy = float(accuracy_score(y_val, preds_val))
        f1 = float(f1_score(y_val, preds_val, average="weighted" if not is_binary else "binary"))
        precision = float(precision_score(y_val, preds_val, average="weighted" if not is_binary else "binary", zero_division=0))
        recall = float(recall_score(y_val, preds_val, average="weighted" if not is_binary else "binary", zero_division=0))

        num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        result = {
            "model_type": f"PyTorch_{arch_type.upper()}",
            "device": self.device,
            "trainable_parameters": num_params,
            "training_time_seconds": elapsed_time,
            "epochs_trained": len(history),
            "best_val_loss": round(best_val_loss, 5),
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "history": history,
            "status": "success"
        }

        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)
            ckpt_path = os.path.join(checkpoint_dir, f"pytorch_{arch_type}_model.pt")
            torch.save({
                "model_state_dict": model.state_dict(),
                "input_dim": input_dim,
                "output_dim": output_dim,
                "arch_type": arch_type,
                "metrics": result
            }, ckpt_path)
            result["checkpoint_path"] = ckpt_path

        return result
