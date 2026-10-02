"""
DataWise AI — Comprehensive Tests for Master Implementation Prompt Features:
1. Iterative Optimization Loop (Graph, Memory, Bounds)
2. Production Readiness 13-Point Checklist & Deployment Gate
3. Safe Model Rollback
4. Ground-Truth Tracking & Performance Degradation Alerting
5. AI Provider Telemetry Dashboard Endpoint
6. Agents (Imbalance, Threshold, Final Model Selection, Audit, Performance)
"""

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from main import app

from graphs.optimization_graph import (
    build_optimization_graph,
    model_candidates_node,
    baseline_training_node,
    cross_validation_leaderboard_node,
    ai_analyzes_results_node,
    train_and_evaluate_node,
    modify_and_retrain_node,
    robustness_test_node,
    compare_models_node,
    final_model_selection_node,
    check_overfit_underfit,
    check_improvement,
)
from graphs.state import create_initial_agent_state
from agents.imbalance_agent import ImbalanceAgent
from agents.threshold_optimization_agent import ThresholdOptimizationAgent
from agents.final_model_selection_agent import FinalModelSelectionAgent
from agents.iterative_optimization_agent import IterativeOptimizationAgent, OptimizationMemory, ExperimentRecord
from agents.performance_monitoring_agent import PerformanceMonitoringAgent
from agents.audit_agent import AuditAgent
from app.ml.production_readiness import ProductionReadinessChecker
from app.api.endpoints.registry import _REGISTRY_DB, _PRODUCTION_POINTERS
from app.api.endpoints.inference import _INFERENCE_LOGS


# ─── 1. Agents Testing ─────────────────────────────────────────────────────────

def test_imbalance_agent_detection(tmp_path):
    # Create synthetic imbalanced dataset (95% 0s, 5% 1s)
    csv_file = tmp_path / "imbalanced.csv"
    data = {"f1": range(100), "target": [0] * 95 + [1] * 5}
    import pandas as pd
    pd.DataFrame(data).to_csv(csv_file, index=False)

    agent = ImbalanceAgent()
    out = agent.run({
        "dataset_path": str(csv_file),
        "parameters": {"target_column": "target"},
    })

    assert out.success is True
    res = out.data
    assert res["is_imbalanced"] is True
    assert res["minority_percentage"] == 5.0
    assert res["recommended_metric"] == "pr_auc" or "f1" in res["recommended_metric"]


def test_threshold_optimization_agent():
    agent = ThresholdOptimizationAgent()
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    # Skewed predicted probabilities where 0.3 is optimal threshold
    y_proba = np.array([0.1, 0.15, 0.2, 0.25, 0.28, 0.32, 0.35, 0.6, 0.8, 0.9])

    res = agent.optimize_threshold(y_true, y_proba, metric="f1")
    assert res.optimal_threshold <= 0.4
    assert res.optimal_f1 > res.default_f1
    assert len(res.evaluation_curve) > 0


def test_final_model_selection_agent():
    agent = FinalModelSelectionAgent()
    candidates = [
        {
            "model_name": "OverfittedModel",
            "cv_mean": 0.92,
            "cv_std": 0.08,
            "train_score": 0.99,
            "test_score": 0.82,  # Large generalization gap
            "metrics": {"f1": 0.82},
            "latency_ms": 25.0,
            "robustness_score": 0.70,
        },
        {
            "model_name": "BalancedChampion",
            "cv_mean": 0.88,
            "cv_std": 0.02,  # Very stable folds
            "train_score": 0.90,
            "test_score": 0.87,  # Small gap
            "metrics": {"f1": 0.87},
            "latency_ms": 10.0,
            "robustness_score": 0.92,
        },
    ]

    decision = agent.rank_candidates(candidates, primary_metric="f1")
    # Section 54: Never simply max(accuracy). The balanced model with low gap and high stability wins!
    assert decision.selected_model == "BalancedChampion"
    assert decision.generalization_gap <= 0.05
    assert decision.cv_stability_score >= 0.80


def test_audit_agent():
    agent = AuditAgent(session_id="test_session")
    rec = agent.record_event(
        event_type="MODEL_DEPLOYED",
        actor_id="admin@datawise.ai",
        project_id="fraud_detection_v1",
        details={"model_version": "v1.0.0"},
        severity="INFO",
    )
    assert rec.event_type == "MODEL_DEPLOYED"
    assert rec.audit_id is not None
    assert len(agent._audit_log) == 1


# ─── 2. Optimization Loop Testing ─────────────────────────────────────────────

def test_iterative_optimization_memory_prevents_repeats():
    memory = OptimizationMemory()
    exp = ExperimentRecord(
        iteration=1,
        hypothesis="Test class weighting",
        dimension_modified="class_weight",
        change_summary={"weight": "balanced"},
        metric_name="f1",
        before_score=0.80,
        after_score=0.82,
        delta=0.02,
        status="KEPT",
        runtime_seconds=1.2,
        reason="Improved recall",
    )
    memory.record(exp)

    # Must detect that this configuration has already been tested
    assert memory.has_tested("class_weight", {"weight": "balanced"}) is True
    assert memory.has_tested("class_weight", {"weight": "other"}) is False


def test_optimization_graph_execution():
    state = create_initial_agent_state(
        dataset_path="mock.csv",
        session_id="test_opt_session",
        target_column="target",
        problem_type="classification",
    )

    # Step 1: Model candidates
    s1 = model_candidates_node(state)
    assert len(s1["candidate_models"]) >= 3

    # Step 2: Baseline training
    s2 = baseline_training_node(s1)
    assert len(s2["training_results"]) == 1

    # Step 3: Cross validation & Leaderboard
    s3 = cross_validation_leaderboard_node(s2)
    assert len(s3["leaderboard"]) >= 2
    assert s3["best_model"] != ""

    # Step 4: AI Analyzes results & selects next experiment
    s4 = ai_analyzes_results_node(s3)
    assert s4["pending_decision"] is not None

    # Step 5: Train & evaluate candidate
    s5 = train_and_evaluate_node(s4)
    assert "candidate_model_evaluated" in s5

    # Step 6: Overfit / Underfit branch check
    branch = check_overfit_underfit(s5)
    assert branch in ("modify_retrain", "robustness_test")

    if branch == "modify_retrain":
        s6 = modify_and_retrain_node(s5)
    else:
        s6 = robustness_test_node(s5)

    # Step 7: Compare against champion
    s7 = compare_models_node(s6)
    assert "last_comparison" in s7
    assert len(s7["optimization_history"]) == 1

    # Step 8: Final Model Selection
    s8 = final_model_selection_node(s7)
    assert s8["best_model"] != ""
    assert "final_model_decision" in s8["evaluation_results"]
    decision = s8["evaluation_results"]["final_model_decision"]
    assert "composite_score" in decision


def test_optimization_loop_bounds():
    state_term = {
        "loop_counters": {
            "opt_iteration": 5,
            "no_improvement_count": 0,
            "start_time": 0.0,
        },
        "last_comparison": {"is_improvement": False},
    }
    assert check_improvement(state_term) == "stop_select"

    import time
    state_cont = {
        "loop_counters": {
            "opt_iteration": 2,
            "no_improvement_count": 1,
            "start_time": time.time(),
        },
        "last_comparison": {"is_improvement": True},
    }
    assert check_improvement(state_cont) == "continue"


# ─── 3. Production Readiness & Registry Testing ───────────────────────────────

def test_production_readiness_checker_all_pass():
    model_data = {
        "feature_columns": ["col1", "col2", "col3"],
        "leakage_report": {"has_leakage": False, "should_halt_training": False},
        "train_score": 0.88,
        "test_score": 0.85,
        "cross_validation_results": {"cv_mean": 0.86, "cv_std": 0.02},
        "robustness_report": {"robustness_score": 0.90},
        "evaluation_results": {"latency_ms": 15.0, "test_score": 0.85},
    }

    report = ProductionReadinessChecker.evaluate(
        model_id="mod_123",
        model_version="v1.0.0",
        state_data=model_data,
        previous_versions=[],
    )
    assert report.is_ready_for_deployment is True
    assert report.status == "READY_FOR_DEPLOYMENT"
    assert report.failed_count == 0
    assert report.passed_count == 13


def test_production_readiness_checker_fails_on_leakage():
    model_data = {
        "feature_columns": ["col1"],
        "leakage_report": {"has_leakage": True, "should_halt_training": True},
        "train_score": 0.88,
        "test_score": 0.85,
    }
    report = ProductionReadinessChecker.evaluate(
        model_id="mod_leaky",
        model_version="v1.0.0",
        state_data=model_data,
    )
    assert report.is_ready_for_deployment is False
    assert report.status == "VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_registry_readiness_and_rollback():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register V1 model
        reg_v1 = await ac.post("/api/v1/models/register", json={
            "project_id": "proj_prod_test",
            "model_name": "GradientBoostingClassifier",
            "version": "v1.0.0",
            "task_type": "classification",
            "feature_columns": ["f1", "f2"],
            "metrics": {"f1": 0.85, "accuracy": 0.87},
        })
        assert reg_v1.status_code == 200
        v1_id = reg_v1.json()["model_id"]

        # 2. Check readiness of V1
        ready_v1 = await ac.get(f"/api/v1/models/{v1_id}/readiness")
        assert ready_v1.status_code == 200
        assert ready_v1.json()["is_ready_for_deployment"] is True

        # 3. Transition V1 to production
        trans_v1 = await ac.post(f"/api/v1/models/{v1_id}/transition", json={
            "target_status": "production",
            "reason": "Initial deployment",
        })
        assert trans_v1.status_code == 200

        # 4. Register V2 model
        reg_v2 = await ac.post("/api/v1/models/register", json={
            "project_id": "proj_prod_test",
            "model_name": "HistGradientBoostingClassifier",
            "version": "v2.0.0",
            "task_type": "classification",
            "feature_columns": ["f1", "f2"],
            "metrics": {"f1": 0.89, "accuracy": 0.90},
        })
        v2_id = reg_v2.json()["model_id"]

        # 5. Transition V2 to production (demotes V1 to archived)
        trans_v2 = await ac.post(f"/api/v1/models/{v2_id}/transition", json={
            "target_status": "production",
            "reason": "Upgraded model",
        })
        assert trans_v2.status_code == 200
        assert _REGISTRY_DB[v1_id]["status"] == "archived"

        # 6. Safe Rollback: Rollback to V1
        rb = await ac.post(f"/api/v1/models/{v1_id}/rollback")
        assert rb.status_code == 200
        assert _REGISTRY_DB[v1_id]["status"] == "production"
        assert _REGISTRY_DB[v2_id]["status"] == "archived"


# ─── 4. Ground-Truth Tracking & Performance Degradation ───────────────────────

@pytest.mark.asyncio
async def test_ground_truth_ingestion_and_degradation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register a model
        reg = await ac.post("/api/v1/models/register", json={
            "project_id": "proj_perf_test",
            "model_name": "FraudClassifier",
            "version": "v1.0.0",
            "task_type": "classification",
            "feature_columns": ["amount", "hour"],
            "metrics": {"f1": 0.90, "accuracy": 0.92},
        })
        m_id = reg.json()["model_id"]

        # Run 4 predictions
        req_ids = []
        for i in range(4):
            pred_resp = await ac.post(f"/api/v1/inference/{m_id}/predict", json={
                "features": {"amount": 100 * (i + 1), "hour": 12}
            })
            req_ids.append(pred_resp.json()["request_id"])

        # Feed ground truth outcomes that cause severe degradation (actual all 0, preds were 1)
        gt_resp = await ac.post(f"/api/v1/inference/{m_id}/ground-truth", json={
            "items": [
                {"request_id": req_ids[0], "ground_truth": 0},
                {"request_id": req_ids[1], "ground_truth": 0},
                {"request_id": req_ids[2], "ground_truth": 0},
                {"request_id": req_ids[3], "ground_truth": 0},
            ]
        })
        assert gt_resp.status_code == 200
        data = gt_resp.json()
        assert data["updated_count"] == 4
        perf = data["performance_report"]
        assert perf is not None
        assert perf["degradation_detected"] is True
        assert perf["action_required"] == "RETRAIN_RECOMMENDED"

        # Check performance endpoint
        p_get = await ac.get(f"/api/v1/inference/{m_id}/performance")
        assert p_get.status_code == 200
        assert p_get.json()["degradation_detected"] is True


# ─── 5. AI Provider Telemetry Dashboard Endpoint ──────────────────────────────

@pytest.mark.asyncio
async def test_ai_providers_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_status" in data
        assert "providers" in data
        assert "gemini" in data["providers"]
        assert "groq" in data["providers"]
        assert "cloudflare" in data["providers"]
        assert "ollama" in data["providers"]
        assert "circuit_state" in data["providers"]["gemini"]
        assert "rate_limit_429s" in data["providers"]["groq"]
