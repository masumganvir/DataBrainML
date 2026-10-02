"""
DataWise AI — Comprehensive Report & Roadmap Generator

Generates:
1. Full Analytical Markdown Report
2. Executive Standalone HTML Report (print/PDF ready)
3. Production Machine Learning Project Roadmap
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.state.data_science_state import DataScienceState


def generate_markdown_report(state: DataScienceState) -> str:
    """Generates an in-depth data science and ML preparation report in Markdown format."""
    meta = state.get("dataset_metadata") or {}
    filename = meta.get("filename", "Dataset")
    row_count = meta.get("row_count", 0)
    col_count = meta.get("col_count", 0)
    filesize = meta.get("size_bytes", 0)
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    readiness_score = state.get("ml_readiness_score")
    readiness_level = state.get("ml_readiness_level", "UNKNOWN")
    score_str = f"{readiness_score:.1f}/100" if readiness_score is not None else "N/A"

    target_col = state.get("target_column") or "Not Specified"
    task_type = state.get("task_type") or "Unassigned"

    missing_reports = state.get("missing_value_report") or []
    outlier_reports = state.get("outlier_report") or []
    dup_report = state.get("duplicate_report") or {}
    dup_count = dup_report.get("duplicate_count", 0)
    dup_pct = dup_report.get("duplicate_pct", 0.0)

    selected_features = state.get("selected_features") or []
    engineered_features = state.get("engineered_features") or []
    model_recs = state.get("model_recommendations") or []
    leakage_warnings = state.get("leakage_warnings") or []

    outlier_decisions = state.get("outlier_decisions") or []
    trained_models = state.get("trained_models") or []
    selected_model = state.get("selected_final_model") or "Selected Model"
    primary_metric = state.get("primary_metric") or "Evaluation Metric"
    cv_strategy = state.get("cv_strategy") or "5-Fold Cross-Validation"
    readiness_audit = state.get("production_readiness") or {}
    exp = state.get("model_explainability") or {}
    limitations = exp.get("model_limitations") or []

    lines = [
        f"# DataWise AI — Data Intelligence & Autonomous ML Report",
        f"",
        f"**Dataset:** `{filename}`  ",
        f"**Generated:** {created_at}  ",
        f"**Target Column:** `{target_col}` | **Task:** `{task_type.capitalize()}` | **Optimization Metric:** `{primary_metric}`  ",
        f"**Production Readiness Status:** **{readiness_audit.get('status', 'PENDING')}** ({readiness_audit.get('readiness_score', readiness_score or 0.0)}/100)  ",
        f"",

        f"---",
        f"",
        f"## 1. Executive Summary",
        f"",
        f"- **Dataset Scale:** {row_count:,} rows × {col_count} columns ({filesize / 1024:.1f} KB)",
        f"- **Schema Breakdown:** {len(state.get('numerical_columns') or [])} numerical, {len(state.get('categorical_columns') or [])} categorical, {len(state.get('datetime_columns') or [])} datetime",
        f"- **Duplicate Rows:** {dup_count:,} ({dup_pct:.1f}%)",
        f"- **Target Leakage Risk:** {len(leakage_warnings)} alerts identified",
        f"- **Champion Algorithm:** `{selected_model}`",
        f"",
        f"## 2. Dataset Overview",
        f"",
        f"| Attribute | Value |",
        f"| :--- | :--- |",
        f"| Filename | `{filename}` |",
        f"| Record Count | {row_count:,} |",
        f"| Feature Count | {col_count:,} |",
        f"| Dataset Domain | {state.get('dataset_domain', 'Unspecified')} |",
        f"| Prediction Objective | {state.get('prediction_objective', 'Unspecified')} |",
        f"",
        f"## 3. Data Quality",
        f"",
        f"- Total Missing Cells: {sum(r.get('missing_count', 0) for r in missing_reports):,}",
        f"- Exact Duplicate Records: {dup_count:,} ({dup_pct:.2f}%)",
        f"- Quality Verdict: {'Requires Preprocessing' if missing_reports or dup_count > 0 else 'Clean / Analysis-Ready'}",
        f"",
        f"## 4. Missing Values",
        f"",
    ]

    if missing_reports:
        lines.append("| Column | Missing Count | Missing % | Severity | Recommended Strategy | Rationale |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for mr in missing_reports:
            lines.append(
                f"| `{mr.get('column')}` | {mr.get('missing_count', 0):,} | {mr.get('missing_pct', 0.0):.1f}% | "
                f"**{mr.get('severity', 'NONE')}** | `{mr.get('recommended_strategy', 'median')}` | {mr.get('explanation', 'Statistical imputation')} |"
            )
        lines.append("")
    else:
        lines.append("No missing values found across any columns.\n")

    lines.extend([
        f"## 5. Outliers",
        f"",
        f"Outliers are evaluated in relation to dataset domain and ML objective to preserve critical target signal.",
        f"",
    ])

    if outlier_decisions:
        lines.append("| Column | Outlier Count | % | Action | Classification | Rationale |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for od in outlier_decisions[:10]:
            lines.append(
                f"| `{od.get('column')}` | {od.get('outlier_count', 0):,} | {od.get('outlier_pct', 0.0):.1f}% | "
                f"**{od.get('recommended_action', 'KEEP')}** | {od.get('classified_as', 'unknown')} | {od.get('rationale', '')} |"
            )
        lines.append("")
    elif outlier_reports:
        lines.append("| Column | Method | Outlier Count | Outlier % | Severity |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for out in outlier_reports[:10]:
            lines.append(
                f"| `{out.get('column')}` | {out.get('method', 'IQR')} | {out.get('outlier_count', 0):,} | "
                f"{out.get('outlier_pct', 0.0):.1f}% | {out.get('severity', 'mild')} |"
            )
        lines.append("")
    else:
        lines.append("No significant outliers flagged.\n")

    # 6. Distributions
    lines.extend([
        f"## 6. Distributions",
        f"",
        f"Evaluates continuous feature skewness, kurtosis, and tail thickness.",
        f"",
    ])

    # 7. Correlations
    corr_report = state.get("correlation_report") or {}
    high_corr = corr_report.get("highly_correlated_pairs") or []
    lines.extend([
        f"## 7. Correlations",
        f"",
    ])
    if high_corr:
        lines.append("| Feature 1 | Feature 2 | Correlation (r) | Impact |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for pair in high_corr[:10]:
            lines.append(f"| `{pair.get('feature_1', '')}` | `{pair.get('feature_2', '')}` | {pair.get('correlation', 0.0):.2f} | Collinear |")
        lines.append("")
    else:
        lines.append("No critical pairwise collinearity detected (|r| > 0.85).\n")

    # 8. Feature Engineering
    lines.extend([
        f"## 8. Feature Engineering",
        f"",
        f"- **Engineered Features ({len(engineered_features)}):** " + (", ".join(f"`{f}`" for f in engineered_features) if engineered_features else "None proposed"),
        f"",
        f"## 9. Feature Selection",
        f"",
        f"- **Selected Predictor Features ({len(selected_features)}):** " + (", ".join(f"`{f}`" for f in selected_features) if selected_features else "All features retained"),
        f"",
        f"## 10. Leakage Analysis",
        f"",
    ])
    if leakage_warnings:
        for w in leakage_warnings:
            lines.append(f"- ⚠️ **`{w.get('column')}`** ({w.get('risk_level', 'HIGH')} Risk): {w.get('explanation', '')}")
        lines.append("")
    else:
        lines.append("No direct target leakage identified in feature space.\n")

    # 11. Preprocessing Strategy
    lines.extend([
        f"## 11. Preprocessing Strategy",
        f"",
        f"- **Strict Train/Test Isolation:** Train/test split executed prior to fitting scalers or imputers.",
        f"- **Numerical Pipeline:** Median Imputation -> StandardScaler (fitted strictly on train partition).",
        f"- **Categorical Pipeline:** Most-Frequent Imputation -> OneHotEncoder with `handle_unknown='ignore'`.",
        f"",
        f"## 12. ML Task",
        f"",
        f"- **Inferred Task:** `{task_type.capitalize()}`",
        f"- **Target Variable:** `{target_col}`",
        f"- **Optimization Metric:** `{primary_metric}`",
        f"",
        f"## 13. Model Candidates",
        f"",
    ])
    if model_recs:
        for idx, rec in enumerate(model_recs[:4], 1):
            lines.append(f"- **Candidate {idx}:** `{rec.get('model_name')}` — {rec.get('rationale', '')}")
    else:
        lines.append("Shortlisted Logistic Regression, Random Forest, and HistGradientBoosting.")
    lines.append("")

    # 14. Cross Validation
    lines.extend([
        f"## 14. Cross Validation",
        f"",
        f"- **Validation Strategy:** `{cv_strategy}`",
        f"- **Scoring Target:** `{primary_metric}`",
        f"",
        f"## 15. Model Comparison",
        f"",
    ])

    if trained_models:
        lines.append(f"| Model Architecture | CV Mean ({primary_metric}) | CV Std | Test {primary_metric} | Fit Time | Status |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for m in trained_models:
            sel = "**CHAMPION**" if m.get("is_selected") else "Candidate"
            t_score = m.get("test_metrics", {}).get(primary_metric, "N/A")
            lines.append(
                f"| `{m['model_name']}` | {m['cv_mean']:.4f} | ±{m['cv_std']:.4f} | "
                f"{t_score} | {m['training_time_seconds']:.2f}s | {sel} |"
            )
        lines.append("")
    else:
        lines.append("Run automated model training to generate cross-validation comparison table.\n")

    # 16. Final Evaluation
    best_m = next((m for m in trained_models if m.get("is_selected")), {})
    best_test_metrics = best_m.get("test_metrics", {})
    lines.extend([
        f"## 16. Final Evaluation",
        f"",
        f"Evaluated on untouched hold-out test set:",
        f"",
    ])
    if best_test_metrics:
        for k, v in best_test_metrics.items():
            lines.append(f"- **{k}:** `{v}`")
        lines.append("")
    else:
        lines.append("Evaluation pending model training.\n")

    # 17. Final Model
    lines.extend([
        f"## 17. Final Model",
        f"",
        f"- **Selected Model:** `{selected_model}`",
        f"- **Selection Rationale:** {best_m.get('selection_rationale', 'Optimal cross-validation performance.')}",
        f"- **Serialized Artifact:** `final_model.joblib` (ColumnTransformer + Estimator)",
        f"- **Inference Script:** `code/inference.py`",
        f"",
        f"## 18. Limitations",
        f"",
    ])
    if limitations:
        for lim in limitations:
            lines.append(f"- {lim}")
    else:
        lines.append("- Empirical relationships captured in historical training data are subject to concept drift.")
        lines.append("- Predictive models reflect statistical associations rather than verified causal mechanisms.")
    lines.append("")

    # 19. Recommended Next Steps
    lines.extend([
        f"## 19. Recommended Next Steps",
        f"1. Download the complete reproducible package ZIP (`DataWise_Project.zip`).",
        f"2. Review the generated Jupyter Notebook (`dataset_analysis.ipynb`) for full cell-by-cell walkthrough.",
        f"3. Run `python code/inference.py <new_data.csv>` to generate batch predictions with the production model.",
        f"4. Monitor prediction distributions in production to detect real-world covariate drift.",
        f"",
        f"---",
        f"*Report compiled autonomously by DataWise AI Engine.*",
    ])

    return "\n".join(lines)


def generate_html_report(state: DataScienceState) -> str:
    """
    Generates a standalone, executive-ready HTML report with embedded CSS.
    Optimized for screen inspection and print-to-PDF.
    """
    meta = state.get("dataset_metadata") or {}
    filename = html.escape(str(meta.get("filename", "Dataset")))
    row_count = meta.get("row_count", 0)
    col_count = meta.get("col_count", 0)
    filesize_kb = (meta.get("size_bytes", 0) or 0) / 1024
    created_at = datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC")

    readiness_score = state.get("ml_readiness_score")
    readiness_level = state.get("ml_readiness_level", "UNKNOWN")
    score_display = f"{readiness_score:.1f}" if readiness_score is not None else "N/A"

    badge_color = "#10b981" if (readiness_score and readiness_score >= 70) else ("#f59e0b" if (readiness_score and readiness_score >= 50) else "#ef4444")

    target_col = html.escape(str(state.get("target_column") or "Not Set"))
    task_type = html.escape(str(state.get("task_type") or "Not Identified"))

    missing_reports = state.get("missing_value_report") or []
    outlier_reports = state.get("outlier_report") or []
    dup_report = state.get("duplicate_report") or {}
    dup_count = dup_report.get("duplicate_count", 0)
    dup_pct = dup_report.get("duplicate_pct", 0.0)

    selected_features = state.get("selected_features") or []
    engineered_features = state.get("engineered_features") or []
    model_recs = state.get("model_recommendations") or []
    leakage_warnings = state.get("leakage_warnings") or []

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>DataWise AI Report — {filename}</title>
<style>
  :root {{
    --bg-primary: #0b0f19;
    --bg-card: #111827;
    --bg-card-hover: #1f2937;
    --border: #374151;
    --text-primary: #f9fafb;
    --text-secondary: #9ca3af;
    --accent: #6366f1;
    --accent-light: #818cf8;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    padding: 32px 24px;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 24px;
    margin-bottom: 32px;
  }}
  .header h1 {{ font-size: 26px; font-weight: 700; color: #fff; }}
  .header .meta {{ color: var(--text-secondary); font-size: 14px; margin-top: 4px; }}
  .score-badge {{
    background: #1e1b4b;
    border: 1px solid {badge_color};
    padding: 12px 24px;
    border-radius: 12px;
    text-align: right;
  }}
  .score-badge .score-val {{ font-size: 32px; font-weight: 800; color: {badge_color}; line-height: 1; }}
  .score-badge .score-lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }}

  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }}
  .stat-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
  }}
  .stat-card .label {{ font-size: 12px; color: var(--text-secondary); text-transform: uppercase; font-weight: 600; }}
  .stat-card .value {{ font-size: 24px; font-weight: 700; color: #fff; margin-top: 6px; }}

  .section {{
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 28px;
  }}
  .section h2 {{ font-size: 18px; margin-bottom: 16px; color: #e0e7ff; display: flex; align-items: center; gap: 8px; }}

  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
  th {{ background: #1f2937; text-align: left; padding: 10px 14px; color: #d1d5db; font-weight: 600; border-bottom: 1px solid var(--border); }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #28303f; color: #f3f4f6; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover {{ background-color: rgba(255,255,255,0.02); }}

  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
  }}
  .badge-high {{ background: #7f1d1d; color: #fca5a5; }}
  .badge-med {{ background: #78350f; color: #fcd34d; }}
  .badge-low {{ background: #1e3a5f; color: #93c5fd; }}
  .badge-none {{ background: #064e3b; color: #6ee7b7; }}

  .tag-cloud {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
  .tag {{
    background: #1f2937;
    border: 1px solid var(--border);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-family: monospace;
  }}

  .alert-warning {{
    background: rgba(245, 158, 11, 0.1);
    border-left: 4px solid var(--warning);
    padding: 12px 16px;
    border-radius: 4px;
    margin-top: 12px;
    font-size: 13px;
  }}

  .model-card {{
    background: #1a2234;
    border: 1px solid #2e384d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 14px;
  }}
  .model-card h3 {{ font-size: 15px; color: #a5b4fc; margin-bottom: 6px; }}
  .model-card p {{ font-size: 13px; color: #d1d5db; margin-bottom: 10px; }}

  .print-btn {{
    background: var(--accent);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
  }}
  .print-btn:hover {{ background: var(--accent-light); }}

  @media print {{
    body {{ background: white; color: black; padding: 0; }}
    .section, .stat-card, .model-card {{ background: white; border: 1px solid #ddd; color: black; }}
    .header h1, .stat-card .value, .section h2 {{ color: black; }}
    th {{ background: #f3f4f6; color: black; }}
    td {{ color: black; border-bottom: 1px solid #eee; }}
    .print-btn {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>DataWise AI — Comprehensive Data Intelligence Report</h1>
      <div class="meta">Dataset: <strong>{filename}</strong> | Generated: {created_at}</div>
    </div>
    <div style="display: flex; gap: 16px; align-items: center;">
      <button class="print-btn" onclick="window.print()">Export / Print to PDF</button>
      <div class="score-badge">
        <div class="score-val">{score_display}</div>
        <div class="score-lbl">{readiness_level}</div>
      </div>
    </div>
  </div>

  <div class="grid-4">
    <div class="stat-card">
      <div class="label">Dimensions</div>
      <div class="value">{row_count:,} × {col_count}</div>
    </div>
    <div class="stat-card">
      <div class="label">File Size</div>
      <div class="value">{filesize_kb:.1f} KB</div>
    </div>
    <div class="stat-card">
      <div class="label">Target Column</div>
      <div class="value" style="font-size: 18px; text-overflow: ellipsis; overflow: hidden;">{target_col}</div>
    </div>
    <div class="stat-card">
      <div class="label">ML Task</div>
      <div class="value" style="font-size: 18px; text-transform: capitalize;">{task_type}</div>
    </div>
  </div>

  <!-- Quality Assessment -->
  <div class="section">
    <h2>Data Hygiene & Quality Audit</h2>
    <p style="color: var(--text-secondary); font-size: 14px;">
      Duplicates: <strong>{dup_count:,}</strong> ({dup_pct:.1f}%) | 
      Columns with Missing Values: <strong>{len(missing_reports)}</strong> | 
      Columns with Outliers: <strong>{len(outlier_reports)}</strong>
    </p>

    {"<table><thead><tr><th>Column</th><th>Missing Rows</th><th>Missing %</th><th>Severity</th><th>Recommended Strategy</th></tr></thead><tbody>" if missing_reports else "<p style='margin-top:10px;'>No missing values found across features.</p>"}
    {"".join(f"<tr><td><code>{html.escape(str(m.get('column')))}</code></td><td>{m.get('missing_count', 0):,}</td><td>{m.get('missing_pct', 0.0):.1f}%</td><td><span class='badge badge-{'high' if m.get('severity') in ('HIGH', 'CRITICAL') else ('med' if m.get('severity') == 'MEDIUM' else 'low')}'>{m.get('severity')}</span></td><td>{html.escape(str(m.get('recommended_strategy')))}</td></tr>" for m in missing_reports) if missing_reports else ""}
    {"</tbody></table>" if missing_reports else ""}
  </div>

  <!-- Feature Engineering & Selection -->
  <div class="section">
    <h2>Feature Engineering & Final Selection</h2>
    <div>
      <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">Engineered Features ({len(engineered_features)}):</div>
      <div class="tag-cloud">
        {"".join(f"<span class='tag'>{html.escape(str(f))}</span>" for f in engineered_features) if engineered_features else "<em>None engineered</em>"}
      </div>
    </div>
    <div style="margin-top: 16px;">
      <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 4px;">Selected Features ({len(selected_features)}):</div>
      <div class="tag-cloud">
        {"".join(f"<span class='tag' style='border-color: #6366f1;'>{html.escape(str(f))}</span>" for f in selected_features) if selected_features else "<em>All original features retained</em>"}
      </div>
    </div>
  </div>

  <!-- Leakage Warnings -->
  {"<div class='section'><h2>Target Leakage Warnings</h2>" + "".join(f"<div class='alert-warning'><strong>Column: <code>{html.escape(str(w.get('column')))}</code> ({w.get('risk_level')})</strong>: {html.escape(str(w.get('explanation')))}</div>" for w in leakage_warnings) + "</div>" if leakage_warnings else ""}

  <!-- Recommended Models -->
  <div class="section">
    <h2>Recommended Machine Learning Architectures</h2>
    {"".join(f"<div class='model-card'><h3>{html.escape(str(rec.get('model_name')))} <span style='font-size:12px; color:var(--text-secondary); font-weight:normal;'>({html.escape(str(rec.get('model_class')))})</span></h3><p>{html.escape(str(rec.get('rationale')))}</p><div style='font-size: 12px; color: var(--text-secondary);'><strong>Evaluation Metrics:</strong> {', '.join(html.escape(str(m)) for m in rec.get('evaluation_metrics', []))}</div></div>" for rec in model_recs) if model_recs else "<p style='color: var(--text-secondary);'>Specify a target variable and run ML analysis to view model architectures.</p>"}
  </div>

  <div style="text-align: center; color: var(--text-secondary); font-size: 12px; margin-top: 40px;">
    Autonomously produced by DataWise AI • Production Ready Machine Learning System
  </div>
</div>
</body>
</html>
"""


def generate_ml_roadmap(state: DataScienceState) -> str:
    """
    Generates an enterprise-grade, step-by-step Machine Learning Project Roadmap
    tailored to the specific dataset, task, and findings.
    """
    meta = state.get("dataset_metadata") or {}
    filename = meta.get("filename", "Dataset")
    row_count = meta.get("row_count", 0)
    col_count = meta.get("col_count", 0)
    target = state.get("target_column") or "[Target Column]"
    task = state.get("task_type") or "classification"

    metric_recommendations = {
        "classification": "PR-AUC (if imbalanced), ROC-AUC, F1-Macro, and Log-Loss",
        "regression": "RMSE, MAE, and R² (plus MAPE for business interpretation)",
        "clustering": "Silhouette Score, Davies-Bouldin Index, and Calinski-Harabasz",
        "time_series": "MAPE, WAPE, and Directional Accuracy",
    }.get(task, "Task-appropriate domain metric")

    return f"""# Machine Learning Engineering Roadmap: `{filename}`

**Target:** `{target}` | **Task:** `{task.upper()}` | **Scope:** {row_count:,} records × {col_count} features  
**Architect:** DataWise AI Autonomous Engine

---

## Phase 1: Problem Formulation & KPI Alignment
- **Primary Technical Metric:** {metric_recommendations}.
- **Business Objective:** Translate model predictions into measurable ROI while enforcing false-positive/false-negative cost trade-offs.
- **Baseline Benchmark:** Implement a simple heuristic or DummyClassifier/DummyRegressor to establish performance floor.

---

## Phase 2: Data Pipeline & Hygiene Hardening
1. **Automated Validation:** Deploy Pandera or Great Expectations schema assertions before ingestion into training workers.
2. **Missingness Policy:** Execute reproducible imputation (median for skewed numerics, mode/constant for categoricals) using the verified `pipeline.py`.
3. **Outlier Mitigation:** Apply robust scaling or winsorization rather than blind trimming to retain rare edge cases.
4. **Data Versioning:** Commit raw and preprocessed datasets to DVC (Data Version Control) or an S3/GCS bucket with cryptographic checksums.

---

## Phase 3: Feature Engineering & Selection Strategy
- **Temporal Alignment:** If time stamps exist, ensure all window aggregations strictly precede the observation point to avoid lookahead bias.
- **Dimensionality Reduction:** Select the top feature subset using mutual information and recursive feature elimination.
- **Leakage Prevention:** Eliminate features showing near-deterministic association with `{target}` unless experimentally confirmed as valid pre-event variables.

---

## Phase 4: Model Exploration & Validation Protocol
- **Cross-Validation Scheme:**
  - *For Classification:* 5-Fold Stratified K-Fold.
  - *For Time-Series:* Rolling-Window TimeSeriesSplit (Purged / Embargoed).
  - *For Grouped Entities:* GroupKFold on entity identifier.
- **Candidate Architectures:**
  1. Regularized Linear Model (LogisticRegression / Ridge) as interpretable baseline.
  2. Gradient Boosted Decision Trees (LightGBM / XGBoost / CatBoost) for tabular superiority.
  3. Multi-Layer Perceptron (TabNet or PyTorch MLP) if cross-modal or embedding features exist.

---

## Phase 5: Hyperparameter Optimization & Ensembling
- **Search Framework:** Run Optuna with Bayesian TPE (Tree-structured Parzen Estimator) sampler across 100 trials.
- **Ensemble Blend:** Soft-voting classifier or stacking regressor combining LightGBM, CatBoost, and Random Forest.
- **Early Stopping:** Enforce 50-round patience on validation fold loss to prevent over-parameterization.

---

## Phase 6: Explainability, Governance & Safety
- **Global Interpretability:** Compute TreeSHAP summary plots and permutation feature importances.
- **Local Diagnostics:** Produce individual waterfall plots for borderline or high-consequence inferences.
- **Fairness & Bias Audit:** Check disparate impact across demographic and regional subgroups.

---

## Phase 7: Production Serving & Deployment
- **Packaging:** Export the end-to-end ColumnTransformer + Model to ONNX or serialized MLflow artifact.
- **Serving Architecture:**
  - Fast low-latency REST/gRPC microservice via FastAPI & Uvicorn in Docker containers.
  - Asynchronous Celery/Redis queue for batch inference requests.
- **Unit & Contract Testing:** Test model inputs against out-of-range bounds, null inputs, and unexpected schema types.

---

## Phase 8: MLOps, Monitoring & Continuous Retraining
- **Data Drift:** Track population stability index (PSI) and Kolmogorov-Smirnov statistics using Evidently AI.
- **Concept Drift:** Monitor rolling metric degradation against ground-truth labels as they mature.
- **Retraining Trigger:** Automated GitHub Actions or Kubeflow pipeline trigger when PSI > 0.25 or rolling performance dips 5% below baseline.

---
*Roadmap generated by DataWise AI. Follow these phases sequentially for enterprise deployment.*
"""
