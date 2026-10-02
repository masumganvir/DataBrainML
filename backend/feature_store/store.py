"""
Agentic AutoML Intelligence Platform — Unified Online & Offline Feature Store
High-throughput sub-millisecond online lookup and immutable offline point-in-time storage.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from loguru import logger

from feature_store.schemas import (
    EntityFeatures,
    FeatureDefinition,
    FeatureStatus,
    FeatureStoreQuery,
)


class FeatureStore:
    """Enterprise Feature Store with dual online (key-value) and offline (time-series) storage."""

    def __init__(self):
        # Feature catalog: {feature_name: FeatureDefinition}
        self._registry: Dict[str, FeatureDefinition] = {}

        # Online store: {entity_id: {feature_name: (value, timestamp)}}
        self._online_store: Dict[str, Dict[str, Any]] = {}
        self._online_timestamps: Dict[str, datetime] = {}

        # Offline store: In-memory/append dataframe of historical feature rows
        self._offline_records: List[Dict[str, Any]] = []

    def register_feature(self, definition: FeatureDefinition):
        """Register a feature definition in the store catalog."""
        self._registry[definition.feature_name] = definition
        logger.info(f"[FeatureStore] Registered feature '{definition.feature_name}' (v{definition.version})")

    def get_feature_definition(self, feature_name: str) -> Optional[FeatureDefinition]:
        return self._registry.get(feature_name)

    def list_features(self) -> List[FeatureDefinition]:
        return list(self._registry.values())

    def write_online_features(
        self,
        entity_id: str,
        features: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ):
        """Write features to the fast online key-value store and append to offline history."""
        ts = timestamp or datetime.utcnow()

        if entity_id not in self._online_store:
            self._online_store[entity_id] = {}

        self._online_store[entity_id].update(features)
        self._online_timestamps[entity_id] = ts

        # Append to offline history
        record = {"entity_id": entity_id, "timestamp": ts, **features}
        self._offline_records.append(record)

    def get_online_features(
        self,
        entity_id: str,
        feature_names: Optional[List[str]] = None,
    ) -> Optional[EntityFeatures]:
        """Sub-millisecond retrieval of active online features for model inference."""
        if entity_id not in self._online_store:
            return None

        all_features = self._online_store[entity_id]
        if feature_names is not None:
            retrieved = {k: all_features[k] for k in feature_names if k in all_features}
        else:
            retrieved = dict(all_features)

        return EntityFeatures(
            entity_id=entity_id,
            feature_values=retrieved,
            last_updated=self._online_timestamps.get(entity_id, datetime.utcnow()),
        )

    def get_batch_online_features(
        self,
        entity_ids: List[str],
        feature_names: Optional[List[str]] = None,
    ) -> List[EntityFeatures]:
        """Batch retrieval of online features."""
        results = []
        for eid in entity_ids:
            feat = self.get_online_features(eid, feature_names)
            if feat:
                results.append(feat)
            else:
                # Return empty defaults if unknown entity
                results.append(
                    EntityFeatures(
                        entity_id=eid,
                        feature_values={fn: 0.0 for fn in (feature_names or [])},
                        last_updated=datetime.utcnow(),
                    )
                )
        return results

    def get_historical_features(
        self,
        entity_ids: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Extract offline features for training datasets."""
        if not self._offline_records:
            return pd.DataFrame()

        df = pd.DataFrame(self._offline_records)
        if entity_ids:
            df = df[df["entity_id"].isin(entity_ids)]
        if start_time:
            df = df[df["timestamp"] >= start_time]
        if end_time:
            df = df[df["timestamp"] <= end_time]

        return df

    def compute_feature_statistics(self, feature_name: str) -> Dict[str, float]:
        """Calculate continuous statistics (mean, std, min, max) for feature drift monitoring."""
        if not self._offline_records:
            return {}

        df = pd.DataFrame(self._offline_records)
        if feature_name not in df.columns:
            return {}

        series = pd.to_numeric(df[feature_name], errors="coerce").dropna()
        if series.empty:
            return {}

        stats = {
            "count": float(len(series)),
            "mean": float(series.mean()),
            "std": float(series.std()) if len(series) > 1 else 0.0,
            "min": float(series.min()),
            "max": float(series.max()),
            "q25": float(series.quantile(0.25)),
            "q50": float(series.median()),
            "q75": float(series.quantile(0.75)),
        }

        # Update registry statistics
        if feature_name in self._registry:
            self._registry[feature_name].statistics = stats

        return stats


feature_store = FeatureStore()
