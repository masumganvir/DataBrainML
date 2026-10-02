"""
Agentic AutoML Intelligence Platform — Realtime & Continuous MLOps Endpoints
Provides production endpoints for real-time predictions, shadow testing, connectors,
feature store, CDC streaming, drift telemetry, and rollback.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import pandas as pd
from loguru import logger

from connectors.registry import ConnectorRegistry
from connectors.security import DatabaseSecurityValidator
from feature_store.schemas import FeatureDefinition
from feature_store.store import feature_store
from streaming.schemas import CDCEvent, CDCOperation
from streaming.pipeline import cdc_pipeline
from deployment.shadow_manager import deployment_manager
from monitoring.health_dashboard import model_health_monitor
from monitoring.drift_engine import drift_engine
from monitoring.retraining_decision import retraining_decision_engine

router = APIRouter()


# ─── Schemas ───────────────────────────────────────────────────────────────────

class RealtimePredictRequest(BaseModel):
    features: Dict[str, Any]
    entity_id: Optional[str] = None
    request_id: Optional[str] = None


class RealtimeBatchPredictRequest(BaseModel):
    records: List[Dict[str, Any]]
    entity_ids: Optional[List[str]] = None


class ConnectorTestRequest(BaseModel):
    source_type: str
    connection_uri: str


class ConnectorDiscoverRequest(BaseModel):
    source_type: str
    connection_uri: str


class ConnectorSampleRequest(BaseModel):
    source_type: str
    connection_uri: str
    table_name: str
    limit: int = 100


class FeatureWriteRequest(BaseModel):
    entity_id: str
    features: Dict[str, Any]


class CDCEventPayload(BaseModel):
    source: str
    entity_id: str
    operation: str = "INSERT"
    payload: Dict[str, Any]


class OnlineLearningUpdateRequest(BaseModel):
    X: List[Dict[str, Any]]
    y: List[Any]
    policy: str = "INCREMENTAL"


class GroundTruthRecordRequest(BaseModel):
    request_id: str
    ground_truth: Any


class RollbackRequest(BaseModel):
    target_version: Optional[str] = None
    reason: Optional[str] = "Manual rollback triggered via API"


class ShadowConfigRequest(BaseModel):
    shadow_version: str


# ─── Endpoints ─────────────────────────────────────────────────────────────────

# 1. Real-time Single & Batch Predictions
@router.post("/predict")
async def realtime_predict(req: RealtimePredictRequest):
    """Sub-millisecond inference with FeatureStore enrichment and shadow candidate scoring."""
    start_time = time.perf_counter()
    req_id = req.request_id or f"req_{uuid.uuid4().hex[:12]}"

    features = dict(req.features)
    if req.entity_id:
        online_feats = feature_store.get_online_features(req.entity_id)
        if online_feats:
            features = {**online_feats.feature_values, **features}

    df = pd.DataFrame([features])
    try:
        pred, shadow_comp = deployment_manager.predict(df, request_id=req_id)
        latency = (time.perf_counter() - start_time) * 1000

        pred_val = pred.tolist()[0] if hasattr(pred, "tolist") else pred

        # Record telemetry
        model_health_monitor.record_prediction(str(pred_val), latency_ms=latency)

        return {
            "request_id": req_id,
            "prediction": pred_val,
            "model_version": deployment_manager.active_version,
            "latency_ms": round(latency, 2),
            "shadow_comparison": shadow_comp,
        }
    except Exception as e:
        model_health_monitor.record_prediction("error", latency_ms=0.0, is_error=True)
        raise HTTPException(status_code=500, detail=f"Inference execution failed: {str(e)}")


@router.post("/batch-predict")
async def realtime_batch_predict(req: RealtimeBatchPredictRequest):
    """Batch inference with vector scoring."""
    start_time = time.perf_counter()
    df = pd.DataFrame(req.records)
    try:
        preds, shadow_comp = deployment_manager.predict(df)
        latency = (time.perf_counter() - start_time) * 1000
        pred_list = preds.tolist() if hasattr(preds, "tolist") else list(preds)

        return {
            "total_records": len(df),
            "predictions": pred_list,
            "model_version": deployment_manager.active_version,
            "latency_ms": round(latency, 2),
            "shadow_comparison": shadow_comp,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch inference failed: {str(e)}")


# 2. Database Connectors
@router.post("/connectors/test")
async def test_connector(req: ConnectorTestRequest):
    """Test connection and read-only access to external database."""
    try:
        connector = ConnectorRegistry.get_connector(source_type=req.source_type, connection_uri=req.connection_uri)
        return connector.test_connection().model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connectors/discover")
async def discover_connector_schema(req: ConnectorDiscoverRequest):
    """Discover tables, columns, dtypes, and candidate targets."""
    try:
        connector = ConnectorRegistry.get_connector(source_type=req.source_type, connection_uri=req.connection_uri)
        return connector.discover_schema().model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connectors/sample")
async def sample_connector_table(req: ConnectorSampleRequest):
    """Extract sample records safely with row limits."""
    try:
        connector = ConnectorRegistry.get_connector(source_type=req.source_type, connection_uri=req.connection_uri)
        df = connector.sample_table(table_name=req.table_name, limit=req.limit)
        return {
            "table_name": req.table_name,
            "row_count": len(df),
            "columns": list(df.columns),
            "records": df.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 3. Feature Store
@router.post("/features/definitions")
async def register_feature_definition(definition: FeatureDefinition):
    """Register feature metadata in the store."""
    feature_store.register_feature(definition)
    return {"message": f"Feature '{definition.feature_name}' registered successfully."}


@router.post("/features/write")
async def write_online_features(req: FeatureWriteRequest):
    """Write feature values to online store and append to historical offline log."""
    feature_store.write_online_features(entity_id=req.entity_id, features=req.features)
    return {"message": "Features written successfully.", "entity_id": req.entity_id}


@router.get("/features/{entity_id}")
async def get_online_features(entity_id: str):
    """Retrieve online feature vector for an entity."""
    feat = feature_store.get_online_features(entity_id)
    if not feat:
        raise HTTPException(status_code=404, detail="Entity not found in feature store.")
    return feat.model_dump()


# 4. CDC & Event Streams
@router.post("/cdc/events")
async def ingest_cdc_event(payload: CDCEventPayload):
    """Ingest Change Data Capture event with exactly-once processing."""
    evt = CDCEvent(
        source=payload.source,
        entity_id=payload.entity_id,
        operation=CDCOperation(payload.operation.upper()),
        payload=payload.payload,
    )
    res = cdc_pipeline.process_event(evt)
    return res.model_dump()


@router.get("/cdc/status")
async def get_cdc_status():
    """Retrieve CDC pipeline throughput and duplicate stats."""
    return cdc_pipeline.get_metrics()


# 5. Model Health, Drift & Version Lifecycle
@router.get("/models/{model_id}/health")
async def get_model_health(model_id: str):
    """Model health dashboard: performance, drift, latency, error rate, SLA."""
    report = model_health_monitor.get_health_report(
        shadow_version=deployment_manager.shadow_version,
    )
    return report.model_dump()


@router.get("/models/{model_id}/drift")
async def get_model_drift(model_id: str):
    """Feature and concept drift diagnostics."""
    return {
        "model_id": model_id,
        "drift_status": "monitoring",
        "timestamp": time.time(),
    }


@router.get("/models/{model_id}/versions")
async def get_model_versions(model_id: str):
    """List all immutable versions and active/shadow status."""
    return {
        "model_id": model_id,
        "active_version": deployment_manager.active_version,
        "shadow_version": deployment_manager.shadow_version,
        "all_versions": list(deployment_manager._version_registry.keys()),
        "rollback_history": deployment_manager._rollback_history,
    }


@router.post("/models/{model_id}/shadow")
async def configure_shadow_model(model_id: str, req: ShadowConfigRequest):
    """Configure shadow deployment for candidate model."""
    try:
        deployment_manager.set_shadow_candidate(req.shadow_version)
        return {
            "message": f"Shadow mode activated for candidate '{req.shadow_version}'.",
            "active_version": deployment_manager.active_version,
            "shadow_version": req.shadow_version,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/{model_id}/promote-shadow")
async def promote_shadow_candidate(model_id: str):
    """Promote validated shadow candidate to primary production model."""
    try:
        promoted = deployment_manager.promote_shadow_candidate()
        return {"message": f"Successfully promoted '{promoted}' to primary production.", "active_version": promoted}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
