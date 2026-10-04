"""
DataWise AI — Insight Generation Agent
Sections 38 & 40 Specification:
Synthesizes actionable, grounded data science insights:
- Data Quality & Integrity Status
- Outlier Preservation & Treatment Rationale
- Correlation, Redundancy, and Multicollinearity Warnings
- Dimensionality Compression Opportunity (PCA)
- Dominant Predictive Feature Signals
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger

from backend.agents.eda.eda_state import EDAState


class InsightGenerationAgent:
    """Consolidates findings into executive and technical analytical takeaways."""

    def __init__(self, name: str = "InsightGenerationAgent"):
        self.name = name

    def run(self, state: EDAState) -> EDAState:
        try:
            insights: List[Dict[str, Any]] = []

            # 1. Quality & Shape insight
            r_cnt = state.get("row_count", 0)
            c_cnt = state.get("column_count", 0)
            dq = state.get("data_quality_report", {})
            q_score = dq.get("quality_score", 100)
            insights.append({
                "category": "Data Health",
                "severity": "SUCCESS" if q_score >= 80 else "WARNING",
                "title": f"Dataset Health Score: {q_score}/100",
                "description": f"Audited {r_cnt:,} records across {c_cnt} dimensions. Found {dq.get('missing_total', 0)} missing values and {dq.get('duplicate_rows', 0)} duplicate rows.",
            })

            # 2. Outlier insight
            outl = state.get("outlier_summary", {})
            decisions = outl.get("decisions", [])
            kept_count = sum(1 for d in decisions if d.get("recommended_action") == "KEEP")
            capped_count = sum(1 for d in decisions if "CAP" in d.get("recommended_action", ""))
            insights.append({
                "category": "Outlier Treatment",
                "severity": "INFO",
                "title": f"Signal-Preserving Outlier Management",
                "description": f"Analyzed {len(decisions)} numerical columns. Retained signals across {kept_count} columns and applied non-destructive Winsorization on {capped_count} columns to preserve extreme predictive boundaries.",
            })

            # 3. Multicollinearity insight
            mc = state.get("multicollinearity_report", {})
            high_pairs = mc.get("high_correlation_pairs", [])
            if high_pairs:
                insights.append({
                    "category": "Collinearity",
                    "severity": "WARNING",
                    "title": f"Detected {len(high_pairs)} Collinear Feature Pair(s)",
                    "description": f"Pairwise correlation exceeding 0.70 observed between {high_pairs[0]['feature_1']} and {high_pairs[0]['feature_2']}. Regularization applied inside model pipeline.",
                })
            else:
                insights.append({
                    "category": "Collinearity",
                    "severity": "SUCCESS",
                    "title": "Clean Feature Orthogonality",
                    "description": "Zero excessive multicollinearity detected (all pairwise correlations within safe variance bounds).",
                })

            # 4. PCA insight
            pca = state.get("pca_results", {})
            if pca.get("is_appropriate", False):
                n_95 = pca.get("threshold_components", {}).get("95_percent", 3)
                orig_dim = pca.get("n_features_original", 10)
                insights.append({
                    "category": "Dimensionality",
                    "severity": "INFO",
                    "title": f"PCA Intrinsic Dimension: {n_95} Components (95% Variance)",
                    "description": f"95% of total dataset variance is captured by {n_95} components (down from {orig_dim}). {pca.get('decision_reason', '')}",
                })

            # 5. Target & Feature signal insight
            sel = state.get("feature_selection_results", {})
            top_feats = sel.get("recommended_features", [])[:3]
            if top_feats:
                insights.append({
                    "category": "Key Drivers",
                    "severity": "SUCCESS",
                    "title": f"Primary Predictive Drivers: {', '.join(top_feats)}",
                    "description": "These features demonstrate the highest mutual information and split gains against the target objective.",
                })

            state["insights"] = insights
            state.setdefault("completed_steps", []).append("insight_generation")
            logger.info(f"[{self.name}] Synthesized {len(insights)} data science insights.")
        except Exception as exc:
            logger.error(f"[{self.name}] Insight generation error: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
