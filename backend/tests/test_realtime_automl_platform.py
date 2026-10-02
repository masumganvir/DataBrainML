"""
Agentic AutoML Intelligence Platform — Comprehensive Test Suite
Tests for Database Connectors, Security Validator, MCP, CDC Streaming, Feature Store,
Online Learning, Drift Detection, Shadow Deployment, Rollback, and Specialized Agents.
"""

import pytest
import sqlite3
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier

from connectors.security import DatabaseSecurityValidator
from connectors.generic_sql import SQLiteConnector
from connectors.registry import ConnectorRegistry
from mcp.server import mcp_service
from mcp.schemas import MCPToolCall
from streaming.schemas import CDCEvent, CDCOperation, ProcessingStatus
from streaming.idempotency import EventIdempotencyTracker
from streaming.pipeline import CDCPipeline
from feature_store.schemas import FeatureDefinition
from feature_store.store import FeatureStore
from ml.online_learning import OnlineLearningEngine, ContinuousLearningPolicy
from monitoring.drift_engine import calculate_psi, DriftDetectionEngine
from monitoring.retraining_decision import RetrainingDecisionEngine, RetrainingAction
from monitoring.health_dashboard import ModelHealthMonitor
from deployment.shadow_manager import ModelDeploymentManager

from agents.user_intent_agent.agent import UserIntentAgent
from agents.database_connector_agent.agent import DatabaseConnectorAgent
from agents.schema_discovery_agent.agent import SchemaDiscoveryAgent
from agents.database_security_agent.agent import DatabaseSecurityAgent
from agents.cdc_ingestion_agent.agent import CDCIngestionAgent
from agents.realtime_prediction_agent.agent import RealtimePredictionAgent
from agents.feature_store_agent.agent import FeatureStoreAgent
from agents.online_learning_agent.agent import OnlineLearningAgent
from agents.model_health_agent.agent import ModelHealthAgent
from agents.concept_drift_agent.agent import ConceptDriftAgent
from agents.production_monitoring_agent.agent import ProductionMonitoringAgent
from agents.retraining_decision_agent.agent import RetrainingDecisionAgent
from agents.model_validation_agent.agent import ModelValidationAgent
from agents.rollback_agent.agent import RollbackAgent
from agents.base import AgentInput


# ─── 1. Database Security & Connectors ─────────────────────────────────────────

def test_database_security_validator_blocks_destructive_sql():
    # DROP statement
    res1 = DatabaseSecurityValidator.validate_query("DROP TABLE users;")
    assert not res1.is_safe
    assert "DROP" in res1.blocked_keywords or "destructive" in res1.violation_reason.lower()

    # TRUNCATE statement
    res2 = DatabaseSecurityValidator.validate_query("TRUNCATE TABLE transactions")
    assert not res2.is_safe

    # Semicolon chaining injection
    res3 = DatabaseSecurityValidator.validate_query("SELECT * FROM users; DELETE FROM users;")
    assert not res3.is_safe

    # Valid SELECT query with automatic LIMIT injection
    res4 = DatabaseSecurityValidator.validate_query("SELECT id, name FROM users", max_rows=500)
    assert res4.is_safe
    assert "LIMIT 500" in res4.sanitized_query.upper()


def test_sqlite_connector_lifecycle(tmp_path):
    db_file = tmp_path / "test_lifecycle.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, balance REAL, churned INTEGER, created_at TEXT);")
    conn.execute("INSERT INTO customers VALUES (1, 'Alice', 1200.5, 0, '2026-01-01');")
    conn.execute("INSERT INTO customers VALUES (2, 'Bob', 450.0, 1, '2026-01-02');")
    conn.commit()
    conn.close()

    uri = f"sqlite:///{db_file}"
    connector = SQLiteConnector(connection_uri=uri, name="sqlite_test")

    # Test connection
    test_res = connector.test_connection()
    assert test_res.success is True
    assert test_res.read_only_verified is True

    # Discover schema
    profile = connector.discover_schema()
    assert profile.total_tables >= 1
    table_names = [t.table_name for t in profile.tables]
    assert "customers" in table_names
    assert any("churned" in t for t in profile.candidate_targets)

    # Sample table
    sample_df = connector.sample_table("customers", limit=10)
    assert len(sample_df) == 2
    assert "balance" in sample_df.columns


# ─── 2. MCP Layer ─────────────────────────────────────────────────────────────

def test_mcp_tool_execution(tmp_path):
    db_file = tmp_path / "test_mcp.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (sku TEXT, price REAL);")
    conn.execute("INSERT INTO items VALUES ('A1', 9.99);")
    conn.commit()
    conn.close()

    uri = f"sqlite:///{db_file}"

    # MCP discover schema tool
    call = MCPToolCall(
        tool_name="mcp_discover_schema",
        arguments={"source_type": "sqlite", "connection_uri": uri},
    )
    res = mcp_service.execute_tool(call)
    assert res.success is True
    assert res.data["total_tables"] >= 1

    # MCP approved query execution
    query_call = MCPToolCall(
        tool_name="mcp_execute_approved_query",
        arguments={"source_type": "sqlite", "connection_uri": uri, "sql_query": "SELECT * FROM items"},
    )
    q_res = mcp_service.execute_tool(query_call)
    assert q_res.success is True
    assert q_res.data["row_count"] == 1

    # MCP blocks malicious query
    bad_call = MCPToolCall(
        tool_name="mcp_execute_approved_query",
        arguments={"source_type": "sqlite", "connection_uri": uri, "sql_query": "DROP TABLE items;"},
    )
    b_res = mcp_service.execute_tool(bad_call)
    assert b_res.success is False


# ─── 3. Streaming & CDC ───────────────────────────────────────────────────────

def test_cdc_idempotency_and_pipeline():
    tracker = EventIdempotencyTracker(ttl_seconds=3600)
    assert not tracker.is_duplicate("evt_101")
    tracker.mark_processed("evt_101")
    assert tracker.is_duplicate("evt_101")

    pipeline = CDCPipeline()
    event = CDCEvent(
        event_id="evt_unique_1",
        source="postgres.public.orders",
        entity_id="order_999",
        operation=CDCOperation.INSERT,
        payload={"amount": 89.5, "status": "completed"},
    )
    res1 = pipeline.process_event(event)
    assert res1.processing_status == ProcessingStatus.PROCESSED

    # Second submission is flagged as DUPLICATE
    res2 = pipeline.process_event(event)
    assert res2.processing_status == ProcessingStatus.DUPLICATE


# ─── 4. Feature Store ─────────────────────────────────────────────────────────

def test_feature_store_online_and_offline():
    store = FeatureStore()
    defn = FeatureDefinition(
        feature_name="tx_velocity_1h",
        entity_key="user_id",
        data_type="float64",
        description="Hourly transaction count",
    )
    store.register_feature(defn)
    assert store.get_feature_definition("tx_velocity_1h") is not None

    # Write online features
    store.write_online_features(
        entity_id="usr_42",
        features={"tx_velocity_1h": 5.0, "avg_amount": 120.0},
    )

    online = store.get_online_features("usr_42")
    assert online is not None
    assert online.feature_values["tx_velocity_1h"] == 5.0

    # Historical extraction
    history_df = store.get_historical_features(["usr_42"])
    assert len(history_df) == 1
    assert "avg_amount" in history_df.columns


# ─── 5. Online / Incremental Learning ─────────────────────────────────────────

def test_online_learning_engine_capability_and_update():
    sgd = SGDClassifier(loss="log_loss", random_state=42)
    rf = RandomForestClassifier(n_estimators=10)

    # Capability check
    assert OnlineLearningEngine.supports_incremental_learning(sgd) is True
    assert OnlineLearningEngine.supports_incremental_learning(rf) is False

    # Seed SGD model with initial fit
    X_init = pd.DataFrame(np.random.randn(20, 4), columns=["f1", "f2", "f3", "f4"])
    y_init = pd.Series(np.random.choice([0, 1], size=20))
    sgd.partial_fit(X_init, y_init, classes=[0, 1])

    # Incremental update on new batch
    X_new = pd.DataFrame(np.random.randn(15, 4), columns=["f1", "f2", "f3", "f4"])
    y_new = pd.Series(np.random.choice([0, 1], size=15))

    updated_model, update_res = OnlineLearningEngine.execute_incremental_update(
        current_model=sgd,
        X_new=X_new,
        y_new=y_new,
        classes=[0, 1],
    )
    assert update_res.success is True
    assert update_res.promoted is True

    # Non-incremental algorithm gracefully rejects update
    _, rf_res = OnlineLearningEngine.execute_incremental_update(
        current_model=rf,
        X_new=X_new,
        y_new=y_new,
    )
    assert rf_res.is_supported is False
    assert rf_res.promoted is False


# ─── 6. Drift Detection & Health Telemetry ────────────────────────────────────

def test_drift_detection_psi_and_ks():
    np.random.seed(42)
    base = np.random.normal(loc=0.0, scale=1.0, size=1000)
    same_dist = np.random.normal(loc=0.0, scale=1.0, size=1000)
    shifted_dist = np.random.normal(loc=2.5, scale=1.0, size=1000)

    # PSI between identical distributions should be small (<0.1)
    psi_stable = calculate_psi(base, same_dist)
    assert psi_stable < 0.10

    # PSI on shifted distribution should indicate severe drift (>0.2)
    psi_drifted = calculate_psi(base, shifted_dist)
    assert psi_drifted > 0.20

    base_s = pd.Series(base)
    shift_s = pd.Series(shifted_dist)
    drift_res = DriftDetectionEngine.compute_numerical_feature_drift(base_s, shift_s)
    assert drift_res["drift_detected"] is True
    assert drift_res["severity"] in ("medium", "high")


def test_retraining_decision_engine():
    # Stable report -> CONTINUE
    dec_stable = RetrainingDecisionEngine.evaluate(
        drift_report={"drift_detected": False, "overall_severity": "none"},
    )
    assert dec_stable.action == RetrainingAction.CONTINUE

    # High drift with sufficient samples -> RETRAIN
    dec_retrain = RetrainingDecisionEngine.evaluate(
        drift_report={"drift_detected": True, "overall_severity": "high"},
        new_samples_count=1500,
        min_retrain_samples=1000,
    )
    assert dec_retrain.action == RetrainingAction.RETRAIN

    # High drift with few samples but online support -> ONLINE_UPDATE
    dec_online = RetrainingDecisionEngine.evaluate(
        drift_report={"drift_detected": True, "overall_severity": "high"},
        new_samples_count=100,
        min_retrain_samples=1000,
        model_supports_online=True,
    )
    assert dec_online.action == RetrainingAction.ONLINE_UPDATE


# ─── 7. Shadow Deployment & Instant Rollback ──────────────────────────────────

class DummyEstimator:
    def __init__(self, multiplier=1.0):
        self.multiplier = multiplier

    def predict(self, X):
        return np.ones(len(X)) * self.multiplier


def test_deployment_manager_shadow_and_rollback():
    mgr = ModelDeploymentManager()
    m1 = DummyEstimator(multiplier=1.0)
    m2 = DummyEstimator(multiplier=2.0)

    mgr.register_version("v1.0.0", m1, set_active=True)
    mgr.register_version("v2.0.0", m2, set_active=False)

    assert mgr.active_version == "v1.0.0"

    # Set candidate in shadow mode
    mgr.set_shadow_candidate("v2.0.0")
    assert mgr.shadow_version == "v2.0.0"

    df_test = pd.DataFrame([[1, 2], [3, 4]])
    active_pred, shadow_meta = mgr.predict(df_test)

    assert active_pred[0] == 1.0  # Production gets active model results
    assert shadow_meta is not None
    assert shadow_meta["shadow_version"] == "v2.0.0"
    assert shadow_meta["predictions_agree"] is False  # 1.0 != 2.0

    # Promote shadow candidate
    promoted = mgr.promote_shadow_candidate()
    assert promoted == "v2.0.0"
    assert mgr.active_version == "v2.0.0"
    assert mgr.shadow_version is None

    # Rollback to v1.0.0
    rolled_back = mgr.rollback()
    assert rolled_back == "v1.0.0"
    assert mgr.active_version == "v1.0.0"


# ─── 8. Specialized Agents Execution ──────────────────────────────────────────

def test_specialized_agents_execution():
    # UserIntentAgent
    intent_agent = UserIntentAgent(session_id="test_sess")
    out_intent = intent_agent.run(AgentInput(
        session_id="test_sess",
        parameters={"prompt": "Detect fraudulent credit card charges with high recall"},
    ))
    assert out_intent.status == "success"
    assert out_intent.data["primary_metric"] == "pr_auc"
    assert out_intent.data["is_rare_event"] is True

    # DatabaseSecurityAgent
    sec_agent = DatabaseSecurityAgent(session_id="test_sess")
    out_sec = sec_agent.run(AgentInput(
        session_id="test_sess",
        parameters={"sql_query": "SELECT customer_id FROM orders"},
    ))
    assert out_sec.status == "success"

    # RetrainingDecisionAgent
    retrain_agent = RetrainingDecisionAgent(session_id="test_sess")
    out_retrain = retrain_agent.run(AgentInput(
        session_id="test_sess",
        parameters={"drift_report": {"drift_detected": False}},
    ))
    assert out_retrain.status == "success"
    assert out_retrain.data["action"] == "CONTINUE"

    # ModelValidationAgent
    val_agent = ModelValidationAgent(session_id="test_sess")
    out_val = val_agent.run(AgentInput(
        session_id="test_sess",
        parameters={
            "model": DummyEstimator(),
            "metrics": {"f1": 0.92},
            "cv_summary": {"mean": 0.91},
            "robustness": {"passed": True},
        },
    ))
    assert out_val.status == "success"
    assert out_val.data["production_ready"] is True
