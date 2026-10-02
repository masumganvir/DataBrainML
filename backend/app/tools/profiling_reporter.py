"""
DataWise AI — Dataset Profiling & HTML Report Generator
Implements Prompt Section 9 & 10:
- Attempts YData Profiling ProfileReport first
- If missing or fails, logs warning and uses platform's fallback profiling engine
- Generates clean, standalone ydata_profile.html and ydata_profile.json
- Profiles each dataset in its dedicated folder
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from loguru import logger

from app.tools.profiler import DatasetProfiler


def generate_dataset_profile_artifacts(
    df: pd.DataFrame,
    output_dir: Path,
    title: str = "Dataset Profiling Report",
) -> Dict[str, str]:
    """
    Produces ydata_profile.html and ydata_profile.json in the specified output directory.
    Follows Section 9 & 10 requirements:
      1. Attempt ydata_profiling
      2. If failure/uninstalled, log warning
      3. Use fallback profiling system
      4. Return paths to created artifacts
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "ydata_profile.html"
    json_path = output_dir / "ydata_profile.json"

    # Step 1: Attempt YData Profiling
    ydata_success = False
    try:
        from ydata_profiling import ProfileReport  # type: ignore
        logger.info(f"Generating YData Profiling report for dataset ({len(df)} rows)...")
        profile = ProfileReport(
            df,
            title=title,
            explorative=True,
            minimal=len(df) > 10000,
        )
        profile.to_file(str(html_path))
        # Export JSON if supported
        try:
            profile_json_str = profile.to_json()
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(profile_json_str)
        except Exception:
            pass
        ydata_success = True
        logger.info("YData Profiling HTML generated successfully.")
    except Exception as exc:
        logger.warning(f"YData Profiling unavailable or failed ({exc}). Using platform fallback profiler.")

    # Step 2 & 3: Platform Fallback Profiling
    if not ydata_success or not html_path.exists():
        profiler = DatasetProfiler(df)
        profile_data = profiler.profile()

        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2, default=str)

        # Generate Comprehensive Standalone HTML
        html_content = _build_fallback_profiling_html(df, profile_data, title)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Fallback profiling report generated at {html_path}")

    return {
        "html_path": str(html_path),
        "json_path": str(json_path),
    }


def _build_fallback_profiling_html(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    title: str,
) -> str:
    """Creates a high-fidelity, interactive, modern dark/light HTML dataset profiling report."""
    total_rows = len(df)
    total_cols = len(df.columns)
    memory_kb = int(df.memory_usage().sum()) / 1024
    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round((missing_cells / max(1, total_rows * total_cols)) * 100, 2)
    duplicate_rows = int(df.duplicated().sum())

    # Build Variable Cards
    variable_cards = []
    for col in df.columns:
        s = df[col]
        n_unique = int(s.nunique())
        n_missing = int(s.isnull().sum())
        miss_p = round((n_missing / max(1, total_rows)) * 100, 1)
        dtype_str = str(s.dtype)
        is_num = pd.api.types.is_numeric_dtype(s)

        stat_pills = f"""
        <div class="stat-pill"><span class="label">Distinct</span><span class="value">{n_unique}</span></div>
        <div class="stat-pill"><span class="label">Missing</span><span class="value">{n_missing} ({miss_p}%)</span></div>
        <div class="stat-pill"><span class="label">Type</span><span class="value">{dtype_str}</span></div>
        """
        if is_num:
            clean = s.dropna()
            mean_val = round(float(clean.mean()), 3) if not clean.empty else 0
            min_val = round(float(clean.min()), 3) if not clean.empty else 0
            max_val = round(float(clean.max()), 3) if not clean.empty else 0
            stat_pills += f"""
            <div class="stat-pill"><span class="label">Mean</span><span class="value">{mean_val}</span></div>
            <div class="stat-pill"><span class="label">Min</span><span class="value">{min_val}</span></div>
            <div class="stat-pill"><span class="label">Max</span><span class="value">{max_val}</span></div>
            """

        variable_cards.append(f"""
        <div class="card">
            <div class="card-header">
                <h3>{col}</h3>
                <span class="badge {'badge-num' if is_num else 'badge-cat'}">{'Numeric' if is_num else 'Categorical'}</span>
            </div>
            <div class="stats-grid">
                {stat_pills}
            </div>
        </div>
        """)

    # Build Sample Rows Table
    head_df = df.head(5).fillna("NaN")
    columns_html = "".join([f"<th>{c}</th>" for c in df.columns])
    rows_html = ""
    for _, row in head_df.iterrows():
        rows_html += "<tr>" + "".join([f"<td>{row[c]}</td>" for c in df.columns]) + "</tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 32px 40px;
        }}
        .header {{
            border-bottom: 1px solid var(--surface-border);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 26px; }}
        .header p {{ margin: 0; color: var(--text-muted); font-size: 14px; }}
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 36px;
        }}
        .overview-box {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 16px;
        }}
        .overview-box .num {{ font-size: 24px; font-weight: 700; color: var(--primary); }}
        .overview-box .lbl {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; margin-top: 4px; }}
        .section-title {{ font-size: 20px; font-weight: 600; margin: 32px 0 16px 0; }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 16px;
        }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
        .card-header h3 {{ margin: 0; font-size: 16px; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-num {{ background: rgba(99, 102, 241, 0.2); color: #818cf8; }}
        .badge-cat {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
        .stats-grid {{ display: flex; flex-wrap: wrap; gap: 12px; }}
        .stat-pill {{ background: rgba(255,255,255,0.04); padding: 6px 12px; border-radius: 6px; font-size: 12px; }}
        .stat-pill .label {{ color: var(--text-muted); margin-right: 6px; }}
        .stat-pill .value {{ font-weight: 600; }}
        .table-wrap {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--surface-border); border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--surface-border); }}
        th {{ background: rgba(255,255,255,0.02); color: var(--text-muted); font-weight: 600; }}
        tr:hover td {{ background: rgba(255,255,255,0.02); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Comprehensive Statistical Profile & Schema Verification</p>
    </div>

    <div class="overview-grid">
        <div class="overview-box">
            <div class="num">{total_rows:,}</div>
            <div class="lbl">Total Observations</div>
        </div>
        <div class="overview-box">
            <div class="num">{total_cols}</div>
            <div class="lbl">Feature Columns</div>
        </div>
        <div class="overview-box">
            <div class="num">{missing_cells} ({missing_pct}%)</div>
            <div class="lbl">Missing Cells</div>
        </div>
        <div class="overview-box">
            <div class="num">{duplicate_rows}</div>
            <div class="lbl">Duplicate Rows</div>
        </div>
        <div class="overview-box">
            <div class="num">{memory_kb:.1f} KB</div>
            <div class="lbl">Memory Footprint</div>
        </div>
    </div>

    <div class="section-title">Variable Profiling</div>
    {"".join(variable_cards)}

    <div class="section-title">Sample Records (First 5 Rows)</div>
    <div class="table-wrap">
        <table>
            <thead><tr>{columns_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</body>
</html>
"""
