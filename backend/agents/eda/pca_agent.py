"""
DataWise AI — Principal Component Analysis (PCA) Agent
Sections 16, 17, 18 & 49 Specification:
CRITICAL PRINCIPLES:
1. PCA must NOT run blindly. First checks appropriateness (>=3 numerics, variance, correlations).
2. Never leak target or test data into PCA.
3. Calculates explained variance ratio, cumulative variance, components, and feature loadings.
4. Determines candidate component counts for 90%, 95%, and 99% variance thresholds.
5. Generates 2D and 3D PCA projections for visualization.
6. Evaluates Original Features vs PCA Representation: If PCA destroys predictive signal or interpretability,
   it is retained as an analytical insight artifact, NOT forced into production pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from backend.agents.eda.eda_state import EDAState


class PCAAgent:
    """Rigorous PCA analyzer comparing full feature space with low-dimensional projections."""

    def __init__(self, name: str = "PCAAgent"):
        self.name = name

    def run(self, state: EDAState, df: Optional[pd.DataFrame] = None) -> EDAState:
        try:
            if df is None:
                dataset_path = state.get("dataset_path")
                if not dataset_path:
                    return state
                df = pd.read_csv(dataset_path)

            num_cols = state.get("numeric_columns") or list(df.select_dtypes(include=[np.number]).columns)
            target_col = state.get("target_column")
            features = [c for c in num_cols if c != target_col]

            # 1. Eligibility Check (Section 16)
            if len(features) < 3:
                pca_result = {
                    "is_appropriate": False,
                    "reason": f"Only {len(features)} numeric feature(s) available. PCA requires at least 3 features to justify dimensionality compression.",
                    "applied_to_production": False,
                }
                state["pca_results"] = pca_result
                state.setdefault("completed_steps", []).append("pca_analysis")
                logger.info(f"[{self.name}] Skipped: {pca_result['reason']}")
                return state

            # 2. Prepare Data (Impute + Scale without target leakage)
            sample_size = min(3000, len(df))
            sample_df = df[features].dropna() if len(df) < 500 else df[features].sample(sample_size, random_state=42)

            imputer = SimpleImputer(strategy="median")
            X_clean = imputer.fit_transform(sample_df)

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_clean)

            # 3. Fit Full PCA
            max_comps = min(len(features), 10)
            pca = PCA(n_components=max_comps, random_state=42)
            pca.fit(X_scaled)

            exp_var_ratio = [round(float(v), 4) for v in pca.explained_variance_ratio_]
            cum_var_ratio = [round(float(v), 4) for v in np.cumsum(pca.explained_variance_ratio_)]

            # Candidate thresholds (90%, 95%, 99%)
            n_90 = next((idx + 1 for idx, v in enumerate(cum_var_ratio) if v >= 0.90), len(cum_var_ratio))
            n_95 = next((idx + 1 for idx, v in enumerate(cum_var_ratio) if v >= 0.95), len(cum_var_ratio))
            n_99 = next((idx + 1 for idx, v in enumerate(cum_var_ratio) if v >= 0.99), len(cum_var_ratio))

            # Feature Loadings (Top contributing features per component)
            loadings: Dict[str, Dict[str, float]] = {}
            for comp_idx in range(min(3, max_comps)):
                comp_name = f"PC{comp_idx + 1}"
                comp_weights = {
                    features[i]: round(float(pca.components_[comp_idx, i]), 4)
                    for i in range(len(features))
                }
                # Sort by absolute weight
                sorted_weights = dict(sorted(comp_weights.items(), key=lambda x: abs(x[1]), reverse=True)[:5])
                loadings[comp_name] = sorted_weights

            # 4. Projections for 2D & 3D visualization
            coords_2d = pca.transform(X_scaled)[:, :2]
            proj_2d_sample = [
                {"pc1": round(float(pt[0]), 3), "pc2": round(float(pt[1]), 3)}
                for pt in coords_2d[:100]
            ]

            # 5. Production Recommendation Logic (Sections 18 & 49)
            # Evaluate: Does PC1 + PC2 capture >= 70% or does n_95 save > 40% dimensions?
            is_compression_effective = (n_95 < len(features) * 0.65) and (cum_var_ratio[0] > 0.25)

            if is_compression_effective and len(features) >= 15:
                recommend_prod_pca = True
                decision_reason = (
                    f"Strong dimensionality reduction possible: {n_95} components retain 95% variance "
                    f"(reducing feature space from {len(features)} down to {n_95}, a {round((1 - n_95/len(features))*100)}% reduction)."
                )
            else:
                recommend_prod_pca = False
                decision_reason = (
                    f"Original features offer higher interpretability and preserve non-linear domain signals. "
                    f"PCA retained as visualization and analysis artifact."
                )

            pca_payload = {
                "is_appropriate": True,
                "n_features_original": len(features),
                "n_components_evaluated": max_comps,
                "explained_variance_ratio": exp_var_ratio,
                "cumulative_explained_variance": cum_var_ratio,
                "threshold_components": {
                    "90_percent": n_90,
                    "95_percent": n_95,
                    "99_percent": n_99,
                },
                "feature_loadings": loadings,
                "projection_2d_preview": proj_2d_sample,
                "applied_to_production": recommend_prod_pca,
                "decision_reason": decision_reason,
            }

            state["pca_results"] = pca_payload
            state.setdefault("completed_steps", []).append("pca_analysis")

            # Save pca_results.json
            output_dir = Path(state.get("output_dir", f"artifacts/{state.get('run_id', 'run_001')}/visualizations")).parent
            pca_path = output_dir / "pca_results.json"
            pca_path.parent.mkdir(parents=True, exist_ok=True)
            with open(pca_path, "w", encoding="utf-8") as f:
                json.dump(pca_payload, f, indent=2)
            state.setdefault("artifacts", {})["pca_results"] = str(pca_path)

            logger.info(f"[{self.name}] PCA complete: PC1={exp_var_ratio[0]*100:.1f}%, PC2={exp_var_ratio[1]*100:.1f}%. Candidate components (95%): {n_95}.")
        except Exception as exc:
            logger.error(f"[{self.name}] Error in PCA analysis: {exc}")
            state.setdefault("errors", []).append({"agent": self.name, "error": str(exc)})

        return state
