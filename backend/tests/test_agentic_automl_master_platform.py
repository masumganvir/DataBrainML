"""
DataWise AI — Master Platform Verification Test Suite
Validates the complete 74-section Master Build Prompt specification:
13 Agent categories, 10 Tool packages, PyTorch Deep Learning engine,
XGBoost/LightGBM integration, Monitoring & Drift, and Pipeline packaging.
"""

import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from agents.base import AgentInput, AgentOutput

# 1. Tools
from app.tools.data_tools import profile_dataset, detect_missing_values
from app.tools.visualization_tools import analyze_distributions, calculate_correlations
from app.tools.preprocessing_tools import detect_outliers_iqr, suggest_encoding, suggest_scaling
from app.tools.feature_tools import generate_interaction_features, select_features
from app.tools.ml_tools import ModelTrainer, detect_target_column
from app.tools.deep_learning_tools import PyTorchModelTrainer, HAS_TORCH
from app.tools.evaluation_tools import detect_overfitting_underfitting
from app.tools.deployment_tools import generate_fastapi_service_code, generate_dockerfile_content
from app.tools.monitoring_tools import calculate_psi, calculate_ks_drift, evaluate_dataset_drift

# 2. Ingestion Agents
from app.agents.ingestion import FileIngestionAgent, DatabaseIngestionAgent, StreamIngestionAgent

# 3. Understanding Agents
from app.agents.understanding import (
    DatasetProfilerAgent,
    SchemaAgent,
    ProblemTypeAgent,
    ModalityAgent,
    DataQualityAgent,
)

# 4. Visualization Agents
from app.agents.visualization import EDAAgent, PlotSelectionAgent, VisualizationAgent

# 5. Preprocessing Agents
from app.agents.preprocessing import (
    MissingValueAgent,
    OutlierAgent,
    EncodingAgent,
    ScalingAgent,
    TransformationAgent,
    LeakageAgent,
)

# 6. Feature Engineering Agents
from app.agents.feature_engineering import (
    FeatureEngineeringAgent,
    FeatureSelectionAgent,
    DimensionalityReductionAgent,
)

# 7. Modeling Agents
from app.agents.modeling import (
    ModelStrategyAgent,
    ClassicalMLAgent,
    DeepLearningAgent,
    NeuralArchitectureAgent,
    TransferLearningAgent,
    TimeSeriesAgent,
    AnomalyDetectionAgent,
)

# 8. Optimization Agents
from app.agents.optimization import (
    ExperimentAgent,
    HyperparameterAgent,
    ComputeOptimizationAgent,
)

# 9. Evaluation Agents
from app.agents.evaluation import (
    EvaluationAgent,
    OverfittingAgent,
    ExplainabilityAgent,
    FairnessAgent,
    ModelValidationAgent,
)

# 10. Deployment Agents
from app.agents.deployment import (
    PackagingAgent,
    APIGenerationAgent,
    DockerAgent,
    DeploymentAgent,
)

# 11. Monitoring Agents
from app.agents.monitoring import (
    ModelMonitoringAgent,
    DriftDetectionAgent,
    DataQualityMonitorAgent,
    RetrainingAgent,
)

# 12. Governance Agents
from app.agents.governance import (
    ModelRegistryAgent,
    AuditAgent,
    ModelGovernanceAgent,
)

# 13. Recovery Agents
from app.agents.recovery import (
    ErrorDetectorAgent,
    ErrorClassifierAgent,
    RootCauseAgent,
    RecoveryPlannerAgent,
    FallbackAgent,
    ValidationAgent,
    ConfidentialityAgent,
)

# 14. Orchestration
from app.agents.orchestration import MasterSupervisorAgent

# 15. Graphs
from app.graphs.deep_learning_graph import build_deep_learning_graph


@pytest.fixture
def sample_csv():
    """Generates a reproducible synthetic dataset for platform testing."""
    np.random.seed(42)
    n = 150
    df = pd.DataFrame({
        "age": np.random.randint(18, 70, size=n),
        "income": np.random.uniform(20000, 120000, size=n),
        "credit_score": np.random.uniform(300, 850, size=n),
        "category": np.random.choice(["Tier1", "Tier2", "Tier3"], size=n),
        "target": np.random.choice([0, 1], size=n)
    })
    # Inject missing and outlier values
    df.loc[5, "income"] = np.nan
    df.loc[10, "credit_score"] = 9999.0

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_tool_packages_functional(sample_csv):
    """Verifies all deterministic tools operate correctly."""
    df = pd.read_csv(sample_csv)

    # Profiler & Missing
    prof = profile_dataset(sample_csv)
    assert prof.total_rows == 150
    missing = detect_missing_values(df)
    assert "income" in missing

    # Outliers
    outliers = detect_outliers_iqr(df)
    assert "credit_score" in outliers.get("column_outliers", {})

    # Distributions & Correlations
    dists = analyze_distributions(df)
    assert "age" in dists["numerical_features"]
    corrs = calculate_correlations(df)
    assert corrs is not None

    # Feature Tools
    new_df = generate_interaction_features(df, max_interactions=3)
    assert new_df.shape[1] >= df.shape[1]

    # Deployment code generation
    api_code = generate_fastapi_service_code("test_model", ["age", "income"])
    assert "POST" in api_code
    assert "/predict" in api_code
    docker_content = generate_dockerfile_content()
    assert "FROM python" in docker_content

    # Drift monitoring
    baseline = np.random.normal(0, 1, 100)
    drifted = np.random.normal(2, 1, 100)
    psi = calculate_psi(baseline, drifted)
    assert psi > 0.1 # Significant drift
    ks = calculate_ks_drift(baseline, drifted)
    assert ks["drift_detected"] is True


def test_pytorch_deep_learning_engine():
    """Verifies PyTorch Tabular MLP neural network training and validation."""
    if not HAS_TORCH:
        pytest.skip("PyTorch not installed")

    np.random.seed(42)
    X = np.random.randn(120, 6)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    trainer = PyTorchModelTrainer(epochs=5, batch_size=16)
    result = trainer.train_tabular_classifier(X[:90], y[:90], X[90:], y[90:], arch_type="mlp")

    assert result["status"] == "success"
    assert "accuracy" in result
    assert result["trainable_parameters"] > 0
    assert len(result["history"]) > 0


def test_all_13_agent_categories(sample_csv):
    """Verifies all 13 agent categories can execute analyze() and return structured AgentOutput."""
    inp = AgentInput(
        session_id="test_sess_001",
        dataset_path=sample_csv,
        parameters={"target_column": "target", "problem_type": "classification"}
    )

    # 1. Ingestion
    out_file = FileIngestionAgent().analyze(inp)
    assert out_file.status == "success"
    assert out_file.data["rows"] == 150

    out_db = DatabaseIngestionAgent().analyze(AgentInput(parameters={"table_name": "users"}))
    assert out_db.status == "success"

    out_stream = StreamIngestionAgent().analyze(AgentInput(parameters={"topic": "events"}))
    assert out_stream.status == "success"

    # 2. Understanding
    out_prof = DatasetProfilerAgent().analyze(inp)
    assert out_prof.status == "success"

    out_schema = SchemaAgent().analyze(inp)
    assert out_schema.status == "success"
    assert "target" in out_schema.data["numerical_features"] or "target" in out_schema.data["categorical_features"]

    out_pt = ProblemTypeAgent().analyze(inp)
    assert out_pt.status == "success"
    assert "classification" in out_pt.data["problem_type"]

    out_mod = ModalityAgent().analyze(inp)
    assert out_mod.data["data_modality"] == "TABULAR"

    out_qual = DataQualityAgent().analyze(inp)
    assert out_qual.status == "success"

    # 3. Visualization
    out_eda = EDAAgent().analyze(inp)
    assert out_eda.status == "success"

    out_plot = PlotSelectionAgent().analyze(inp)
    assert out_plot.status == "success"

    out_vis = VisualizationAgent().analyze(AgentInput(dataset_path=sample_csv, parameters={"plot_type": "correlation_heatmap"}))
    assert out_vis.status == "success"

    # 4. Preprocessing
    out_miss = MissingValueAgent().analyze(inp)
    assert out_miss.status == "success"

    out_outlier = OutlierAgent().analyze(inp)
    assert out_outlier.status in ["success", "needs_approval"]

    out_enc = EncodingAgent().analyze(inp)
    assert out_enc.status == "success"

    out_scale = ScalingAgent().analyze(inp)
    assert out_scale.status == "success"

    out_trans = TransformationAgent().analyze(inp)
    assert out_trans.status == "success"

    out_leak = LeakageAgent().analyze(inp)
    assert out_leak.status in ["success", "warning"]

    # 5. Feature Engineering
    out_fe = FeatureEngineeringAgent().analyze(inp)
    assert out_fe.status == "success"

    out_fs = FeatureSelectionAgent().analyze(inp)
    assert out_fs.status == "success"

    out_dim = DimensionalityReductionAgent().analyze(inp)
    assert out_dim.status == "success"

    # 6. Modeling
    out_strat = ModelStrategyAgent().analyze(inp)
    assert out_strat.status == "success"

    out_ml = ClassicalMLAgent().analyze(inp)
    assert out_ml.status == "success"
    assert "best_model_name" in out_ml.data

    out_dl = DeepLearningAgent().analyze(AgentInput(dataset_path=sample_csv, parameters={"target_column": "target"}))
    assert out_dl.status in ["success", "warning"]

    out_arch = NeuralArchitectureAgent().analyze(AgentInput(parameters={"num_features": 5}))
    assert out_arch.status == "success"

    out_tl = TransferLearningAgent().analyze(AgentInput())
    assert out_tl.status == "success"

    out_ts = TimeSeriesAgent().analyze(AgentInput())
    assert out_ts.status == "success"

    out_ad = AnomalyDetectionAgent().analyze(AgentInput())
    assert out_ad.status == "success"

    # 7. Optimization
    out_exp = ExperimentAgent().analyze(AgentInput(parameters={"model_name": "Random Forest"}))
    assert out_exp.status == "success"

    out_opt = HyperparameterAgent().analyze(AgentInput(parameters={"model_name": "Random Forest"}))
    assert out_opt.status == "success"

    out_comp = ComputeOptimizationAgent().analyze(AgentInput(parameters={"dataset_rows": 150}))
    assert out_comp.status == "success"

    # 8. Evaluation
    out_eval = EvaluationAgent().analyze(AgentInput())
    assert out_eval.status == "success"

    out_over = OverfittingAgent().analyze(AgentInput(parameters={"train_score": 0.99, "test_score": 0.70}))
    assert out_over.status == "warning"
    assert "Overfitting" in out_over.data["diagnosis"]

    out_exp_agent = ExplainabilityAgent().analyze(AgentInput(parameters={"features": ["age", "income"]}))
    assert out_exp_agent.status == "success"

    out_fair = FairnessAgent().analyze(AgentInput())
    assert out_fair.status == "success"

    out_val = ModelValidationAgent().analyze(AgentInput())
    assert out_val.data["deployable"] is True

    # 9. Deployment
    out_pkg = PackagingAgent().analyze(AgentInput(parameters={"model_name": "best_model"}))
    assert out_pkg.status == "success"

    out_api = APIGenerationAgent().analyze(AgentInput(parameters={"model_name": "best_model"}))
    assert out_api.status == "success"

    out_dock = DockerAgent().analyze(AgentInput())
    assert out_dock.status == "success"

    out_dep = DeploymentAgent().analyze(AgentInput(parameters={"approved": True, "environment": "staging"}))
    assert out_dep.status == "success"

    # 10. Monitoring
    out_mon = ModelMonitoringAgent().analyze(AgentInput())
    assert out_mon.status == "success"

    out_drift = DriftDetectionAgent().analyze(AgentInput(dataset_path=sample_csv))
    assert out_drift.status == "success"

    out_qual_mon = DataQualityMonitorAgent().analyze(AgentInput())
    assert out_qual_mon.status == "success"

    out_retrain = RetrainingAgent().analyze(AgentInput())
    assert out_retrain.status == "success"

    # 11. Governance
    out_reg = ModelRegistryAgent().analyze(AgentInput())
    assert out_reg.status == "success"

    out_audit = AuditAgent().analyze(AgentInput())
    assert out_audit.status == "success"

    out_gov = ModelGovernanceAgent().analyze(AgentInput())
    assert out_gov.status == "success"

    # 12. Recovery & Confidentiality
    out_err = ErrorDetectorAgent().analyze(AgentInput(parameters={"error_message": "Matrix singular"}))
    assert out_err.status == "success"

    out_clf = ErrorClassifierAgent().analyze(AgentInput(parameters={"error_message": "MemoryError"}))
    assert out_clf.data["category"] == "RESOURCE_EXHAUSTION"

    out_rc = RootCauseAgent().analyze(AgentInput())
    assert out_rc.status == "success"

    out_plan = RecoveryPlannerAgent().analyze(AgentInput(parameters={"category": "RESOURCE_EXHAUSTION"}))
    assert out_plan.status == "success"

    out_fall = FallbackAgent().analyze(AgentInput())
    assert out_fall.status == "success"

    out_val_rec = ValidationAgent().analyze(AgentInput())
    assert out_val_rec.status == "success"

    # Confidentiality check
    raw_secret_text = "Database connection: postgresql://admin:secret123@localhost:5432/db and API key AIzaSy_TEST_MOCK_API_KEY_FOR_REDACTION"
    out_conf = ConfidentialityAgent().analyze(AgentInput(parameters={"text": raw_secret_text}))
    assert "[REDACTED_PASS]" in out_conf.data["sanitized_text"]
    assert "[REDACTED_API_KEY]" in out_conf.data["sanitized_text"]
    assert "secret123" not in out_conf.data["sanitized_text"]

    # 13. Orchestration
    out_sup = MasterSupervisorAgent().analyze(AgentInput(parameters={"current_stage": "UNDERSTANDING"}))
    assert out_sup.status == "success"
    assert out_sup.data["next_recommended_stage"] == "QUALITY_ASSESSMENT"


def test_deep_learning_graph_execution():
    """Verifies that the compiled LangGraph for Deep Learning executes correctly."""
    graph = build_deep_learning_graph()
    initial_state = {
        "dataset_rows": 1200,
        "current_step": "START",
        "deep_learning_allowed": False
    }
    final_state = graph.invoke(initial_state)
    assert final_state["deep_learning_allowed"] is True
    assert final_state["current_step"] == "DL_EVALUATION"
    assert "deep_learning_metrics" in final_state
