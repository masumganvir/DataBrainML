"""
DataWise AI — Multi-Agent System Programmatic Walkthrough
Demonstrates end-to-end multi-agent orchestration on a test dataset.
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.agents import multi_agent_coordinator
from app.graph.workflow import run_analysis_workflow
from app.state.data_science_state import DataScienceState


def run_demo():
    print("=" * 70)
    print("  DataWise AI — Autonomous Multi-Agent Preparation System")
    print("=" * 70)

    # 1. Inspect registered agents
    print("\n[1] Registered Domain Agents:")
    agents = multi_agent_coordinator.list_agents()
    for ag in agents:
        print(f"  • {ag['name']:<25} | {ag['role']}")

    # 2. Select test dataset
    dataset_path = str(Path(__file__).parent.parent / "data" / "test_datasets" / "imbalanced_classification.csv")
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    print(f"\n[2] Initializing State for Dataset:\n  {dataset_path}")
    state: DataScienceState = {
        "session_id": "demo_session_001",
        "dataset_path_original": dataset_path,
        "dataset_path_analysis": dataset_path,
        "current_stage": "INGEST",
        "completed_stages": [],
        "errors": [],
        "user_decisions": [],
    }

    # 3. Ingestion & Profiling
    print("\n[3] Ingestion & Profiling:")
    state = multi_agent_coordinator.intake_agent.run(state)
    print(f"  Rows: {state.get('row_count_current')} | Columns: {state.get('column_count_current')}")

    state = multi_agent_coordinator.profiling_agent.run(state)
    print(f"  Numerical Columns:   {state.get('numerical_columns')}")
    print(f"  Categorical Columns: {state.get('categorical_columns')}")

    # 4. Quality & Hygiene Audit
    print("\n[4] Data Quality & Hygiene:")
    state = multi_agent_coordinator.quality_agent.run(state)
    missing = state.get("missing_value_report", [])
    cols_with_missing = [m for m in missing if m.get("missing_count", 0) > 0]
    print(f"  Columns with missing values: {len(cols_with_missing)}")
    for m in cols_with_missing[:3]:
        print(f"    - {m['column']}: {m['missing_pct']}% missing -> Strategy: {m.get('recommended_strategy')}")

    # 5. Outliers
    print("\n[5] Outlier Detection:")
    state = multi_agent_coordinator.outlier_agent.run(state)
    outliers = state.get("outlier_report", [])
    cols_with_outliers = [o for o in outliers if o.get("outlier_count", 0) > 0]
    print(f"  Columns with outliers: {len(cols_with_outliers)}")

    # 6. Feature Engineering & Selection
    print("\n[6] Feature Engineering & Selection:")
    state = multi_agent_coordinator.feature_engineering_agent.run(state)
    fe_ops = state.get("feature_engineering_plan", [])
    print(f"  Proposed Engineered Features: {len(fe_ops)}")
    for op in fe_ops[:3]:
        print(f"    - {op.get('operation')}: {op.get('rationale')}")

    state = multi_agent_coordinator.feature_selection_agent.run(state)
    selected = state.get("selected_features", [])
    print(f"  Selected High-Importance Features ({len(selected)}): {selected[:6]}...")

    # 7. ML Readiness & Leakage Audit
    print("\n[7] Target Detection & ML Readiness:")
    state = multi_agent_coordinator.ml_readiness_agent.run(state)
    print(f"  Target candidates: {state.get('target_candidates')}")
    print(f"  Leakage alerts:    {len(state.get('leakage_warnings', []))}")

    # 8. Pipeline Builder
    print("\n[8] Scikit-Learn Pipeline Generation:")
    state = multi_agent_coordinator.pipeline_builder_agent.run(state)
    code = state.get("generated_pipeline_code", "")
    print(f"  Synthesized Code: {len(code)} characters")
    print("  --- Code Preview ---")
    print("\n".join(code.splitlines()[:25]))
    print("  ...")

    # 9. ML Recommendations
    print("\n[9] ML Model Recommendations:")
    state = multi_agent_coordinator.ml_recommendation_agent.run(state)
    print(f"  ML Readiness Score: {state.get('ml_readiness_score')}/100 ({state.get('ml_readiness_level')})")
    for rec in state.get("model_recommendations", []):
        print(f"  ★ Model: {rec.get('model_name')}")
        print(f"    Rationale: {rec.get('rationale')}")

    # 10. Reports
    print("\n[10] Report Synthesis:")
    md_report = multi_agent_coordinator.report_agent.generate_markdown(state)
    html_report = multi_agent_coordinator.report_agent.generate_html(state)

    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "demo_report.md").write_text(md_report, encoding="utf-8")
    (output_dir / "demo_report.html").write_text(html_report, encoding="utf-8")
    print(f"  Executive Markdown & HTML reports written to {output_dir}")

    print("\n" + "=" * 70)
    print("  Multi-Agent Pipeline Finished Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
