"""
DataWise AI — EDA Report Agent
Sections 36 & 47 Specification:
Generates:
1. EDA_Report.html — Comprehensive executive and technical HTML report with embedded visual plots, KPI cards, and data science findings.
2. eda_summary.json — Complete structured analytical export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.agents.eda.eda_state import EDAState


class EDAReportAgent:
    """Compiles the final standalone HTML report and structured JSON summary."""

    def __init__(self, name: str = "EDAReportAgent"):
        self.name = name

    def run(self, state: EDAState) -> EDAState:
        try:
            output_dir = Path(state.get("output_dir", f"artifacts/{state.get('run_id', 'run_001')}/visualizations")).parent
            reports_dir = output_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            # 1. Build eda_summary.json (Section 47)
            summary_payload = {
                "dataset_id": state.get("dataset_id"),
                "project_id": state.get("project_id"),
                "run_id": state.get("run_id"),
                "target_column": state.get("target_column"),
                "task_type": state.get("task_type"),
                "dataset_summary": {
                    "rows": state.get("row_count"),
                    "columns": state.get("column_count"),
                    "numeric_columns": state.get("numeric_columns"),
                    "categorical_columns": state.get("categorical_columns"),
                    "datetime_columns": state.get("datetime_columns"),
                },
                "data_quality": state.get("data_quality_report"),
                "outliers": state.get("outlier_summary"),
                "distributions": state.get("distribution_summary"),
                "correlations": state.get("correlation_summary"),
                "multicollinearity": state.get("multicollinearity_report"),
                "PCA": state.get("pca_results"),
                "dimensionality_reduction": state.get("dimensionality_results"),
                "feature_extraction": state.get("feature_extraction_results"),
                "feature_selection": state.get("feature_selection_results"),
                "visualizations": [
                    {k: v for k, v in vis.items() if k != "image_base64"}
                    for vis in state.get("visualization_results", [])
                ],
                "insights": state.get("insights", []),
                "warnings": state.get("warnings", []),
                "recommendations": state.get("recommendations", [
                    "Proceed with robust scaling and leak-free imputation inside ColumnTransformer.",
                    "Preserve critical extreme observations; avoid blind row deletion.",
                    "Incorporate top-ranked mutual information features into training pipeline.",
                ]),
            }

            eda_json_path = output_dir / "eda_summary.json"
            with open(eda_json_path, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2)
            state.setdefault("artifacts", {})["eda_summary"] = str(eda_json_path)

            # 2. Build EDA_Report.html (Section 36)
            vis_cards_html = ""
            for v in state.get("visualization_results", []):
                img_src = v.get("image_base64") or ""
                vis_cards_html += f"""
                <div class="card vis-card">
                  <div class="vis-header">
                    <span class="badge badge-seq">#{v.get('sequence', 0):02d}</span>
                    <h3 class="vis-title">{v.get('title', 'Chart')}</h3>
                    <span class="badge badge-priority">{v.get('priority', 'HIGH')}</span>
                  </div>
                  <div class="vis-body">
                    {f'<img src="{img_src}" alt="{v.get("title")}" class="vis-img" />' if img_src else '<div class="no-img">Plot Generated</div>'}
                  </div>
                  <div class="vis-footer">
                    <p class="vis-desc"><strong>Purpose:</strong> {v.get('description', '')}</p>
                    <div class="vis-insight">💡 <strong>Key Finding:</strong> {v.get('key_insight', '')}</div>
                  </div>
                </div>
                """

            insights_html = ""
            for ins in state.get("insights", []):
                insights_html += f"""
                <div class="insight-box insight-{ins.get('severity', 'INFO').lower()}">
                  <div class="insight-header">
                    <span class="insight-cat">{ins.get('category', 'Insight')}</span>
                    <strong class="insight-title">{ins.get('title', '')}</strong>
                  </div>
                  <p class="insight-desc">{ins.get('description', '')}</p>
                </div>
                """

            pca_data = state.get("pca_results", {})
            pca_info_html = ""
            if pca_data.get("is_appropriate"):
                pca_info_html = f"""
                <div class="card">
                  <h2>Principal Component Analysis (PCA)</h2>
                  <p><strong>Status:</strong> Evaluated ({pca_data.get('n_features_original')} original features &rarr; {pca_data.get('threshold_components', {}).get('95_percent', 3)} components for 95% variance).</p>
                  <p><strong>Production Recommendation:</strong> {'Included in pipeline' if pca_data.get('applied_to_production') else 'Retained as analytical visualization artifact (Preserves interpretability)'}.</p>
                  <p><em>{pca_data.get('decision_reason', '')}</em></p>
                </div>
                """

            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EDA & Visual Intelligence Report — {state.get('project_id', 'DataWise')}</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card: #111827;
      --border: #1f293d;
      --primary: #6366f1;
      --primary-light: #818cf8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    body {{
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      line-height: 1.5;
    }}
    .container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }}
    header {{
      margin-bottom: 32px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 24px;
    }}
    .eyebrow {{
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--primary-light);
      font-weight: 800;
    }}
    h1 {{
      font-size: 2.2rem;
      font-weight: 800;
      margin: 6px 0 12px;
      letter-spacing: -0.02em;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .kpi-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }}
    .kpi-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
      letter-spacing: 0.05em;
    }}
    .kpi-value {{
      font-size: 1.8rem;
      font-weight: 800;
      margin-top: 4px;
      font-family: 'JetBrains Mono', monospace;
      color: var(--primary-light);
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .vis-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(560px, 1fr));
      gap: 24px;
      margin-top: 24px;
    }}
    .vis-card {{
      display: flex;
      flex-direction: column;
      justifyContent: space-between;
    }}
    .vis-header {{
      display: flex;
      align-items: center;
      justifyContent: space-between;
      margin-bottom: 16px;
    }}
    .vis-title {{
      font-size: 1.05rem;
      font-weight: 700;
      margin: 0;
      flex: 1;
      padding: 0 12px;
    }}
    .badge {{
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 6px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .badge-seq {{
      background: rgba(99, 102, 241, 0.2);
      color: var(--primary-light);
    }}
    .badge-priority {{
      background: rgba(16, 185, 129, 0.2);
      color: var(--success);
    }}
    .vis-img {{
      width: 100%;
      height: auto;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #0f172a;
    }}
    .vis-footer {{
      margin-top: 14px;
    }}
    .vis-desc {{
      font-size: 0.85rem;
      color: var(--muted);
      margin: 0 0 8px;
    }}
    .vis-insight {{
      font-size: 0.86rem;
      color: #e2e8f0;
      background: rgba(99, 102, 241, 0.1);
      border-left: 3px solid var(--primary);
      padding: 8px 12px;
      border-radius: 4px;
    }}
    .insight-box {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 20px;
      margin-bottom: 12px;
    }}
    .insight-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 4px;
    }}
    .insight-cat {{
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 800;
      color: var(--primary-light);
    }}
    .insight-title {{
      font-size: 0.95rem;
      color: #fff;
    }}
    .insight-desc {{
      font-size: 0.86rem;
      color: var(--muted);
      margin: 0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="eyebrow">DataWise Autonomous Intelligence</div>
      <h1>Exploratory Data Analysis & Visual Diagnostic Report</h1>
      <p style="color: var(--muted); margin: 0;">Project: <strong>{state.get('project_id', 'proj')}</strong> • Run: <strong>{state.get('run_id', 'run_001')}</strong> • Target: <strong>{state.get('target_column', 'None')}</strong> ({state.get('task_type', 'Auto')})</p>
    </header>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Observations</div>
        <div class="kpi-value">{state.get('row_count', 0):,}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Features</div>
        <div class="kpi-value">{state.get('column_count', 0)}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Data Health Score</div>
        <div class="kpi-value" style="color: var(--success);">{state.get('data_quality_report', {}).get('quality_score', 100)}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Missing Cells</div>
        <div class="kpi-value">{state.get('missing_summary', {}).get('total_missing', 0)}</div>
      </div>
    </div>

    <h2>Executive Data Science Insights</h2>
    <div style="margin-bottom: 32px;">
      {insights_html}
    </div>

    {pca_info_html}

    <h2>Sequence-Wise Visualization Gallery ({len(state.get('visualization_results', []))} Visualizations)</h2>
    <div class="vis-grid">
      {vis_cards_html}
    </div>
  </div>
</body>
</html>
"""

            eda_html_path = output_dir / "EDA_Report.html"
            eda_html_rep_path = reports_dir / "EDA_Report.html"
            with open(eda_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            with open(eda_html_rep_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            state.setdefault("artifacts", {})["eda_report_html"] = str(eda_html_path)
            state.setdefault("completed_steps", []).append("eda_report_generation")
            logger.info(f"[{self.name}] Generated EDA_Report.html and eda_summary.json successfully.")
        except Exception as exc:
            logger.error(f"[{self.name}] EDA report generation error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
