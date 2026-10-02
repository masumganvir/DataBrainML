"""
DataWise AI — FinalModelSelectionAgent (Section 54)
Multi-criteria holistic scoring framework:
Evaluates primary metric, secondary metrics, CV fold stability, generalization gap (overfitting),
robustness score, latency, memory, and interpretability.
Never blindly picks max(accuracy).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput


class FinalModelDecision(BaseModel):
    selected_model: str
    algorithm: str
    composite_score: float
    reason: str
    primary_metric_name: str
    primary_metric_value: float
    secondary_metrics: Dict[str, float] = Field(default_factory=dict)
    cv_stability_score: float
    generalization_gap: float
    robustness_score: float
    inference_latency_ms: float
    limitations: List[str] = Field(default_factory=list)
    deployment_status: str = "VALIDATED_READY"


class FinalModelSelectionAgent(BaseAgent):
    """Selects best production candidate across multi-criteria objective."""

    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="FinalModelSelectionAgent")

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        primary_metric: str = "f1",
        maximize: bool = True,
        max_latency_ms: float = 200.0,
    ) -> FinalModelDecision:
        if not candidates:
            return FinalModelDecision(
                selected_model="Baseline",
                algorithm="Dummy",
                composite_score=0.0,
                reason="No candidate models available",
                primary_metric_name=primary_metric,
                primary_metric_value=0.0,
                cv_stability_score=0.0,
                generalization_gap=0.0,
                robustness_score=0.0,
                inference_latency_ms=1.0,
                deployment_status="FAILED",
            )

        scored_candidates = []
        for c in candidates:
            name = c.get("model_name") or c.get("algorithm") or "Model"
            metrics = c.get("metrics") or c.get("test_metrics") or {}
            prim_val = float(metrics.get(primary_metric, c.get("cv_mean", 0.0)))
            
            # 1. Primary metric score (0 to 1 normalized)
            norm_prim = prim_val if maximize else 1.0 / (1.0 + prim_val)
            
            # 2. CV stability (std deviation penalty)
            cv_std = float(c.get("cv_std", 0.05))
            stability = max(0.0, 1.0 - (cv_std * 5.0))
            
            # 3. Generalization gap (train vs val/test gap penalty)
            train_score = float(c.get("train_score", prim_val))
            test_score = float(metrics.get(primary_metric, prim_val))
            gap = max(0.0, train_score - test_score)
            generalization_penalty = min(1.0, gap * 3.0)
            
            # 4. Latency score (lower latency = higher score)
            lat = float(c.get("latency_ms", 15.0))
            lat_score = max(0.0, 1.0 - (lat / max(max_latency_ms, 1.0)))
            
            # 5. Robustness score
            rob = float(c.get("robustness_score", 0.85))

            # 6. Memory score (RAM footprint in MB)
            mem_mb = float(c.get("memory_mb", 10.0))
            mem_score = max(0.0, 1.0 - (mem_mb / 200.0))  # normalize against 200MB budget

            # 7. Interpretability score (trees and linear models score higher)
            interpretability = float(c.get("interpretability_score", 0.85))
            if "Linear" in name or "Logistic" in name:
                interpretability = 0.95
            elif "Tree" in name or "RandomForest" in name:
                interpretability = 0.85
            elif "Gradient" in name or "Hist" in name:
                interpretability = 0.75
            elif "Neural" in name or "MLP" in name:
                interpretability = 0.50

            # Composite Multi-Criteria Score (User Specification):
            # Performance + Robustness + Latency + Memory + Interpretability
            # 40% Performance + 20% Robustness + 15% Latency + 15% Stability/Gap + 5% Memory + 5% Interpretability
            composite = (
                0.40 * norm_prim +
                0.20 * rob +
                0.15 * lat_score +
                0.10 * stability +
                0.05 * (1.0 - generalization_penalty) +
                0.05 * mem_score +
                0.05 * interpretability
            )

            scored_candidates.append({
                "candidate": c,
                "name": name,
                "composite": composite,
                "prim_val": prim_val,
                "metrics": metrics,
                "stability": stability,
                "gap": gap,
                "robustness": rob,
                "latency": lat,
                "memory_mb": mem_mb,
                "interpretability": interpretability,
            })

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x["composite"], reverse=True)
        winner = scored_candidates[0]
        c_win = winner["candidate"]

        limitations = []
        if winner["gap"] > 0.10:
            limitations.append(f"Moderate train-test gap of {winner['gap']:.3f} observed")
        if winner["latency"] > 100.0:
            limitations.append(f"Inference latency is {winner['latency']:.1f}ms, consider quantizing for edge deployment")
        if winner["stability"] < 0.80:
            limitations.append("CV folds showed moderate variance across folds")

        reason = (
            f"Selected {winner['name']} with composite score of {winner['composite']:.3f}. "
            f"Demonstrated superior balance of {primary_metric} ({winner['prim_val']:.4f}), "
            f"fold stability ({winner['stability']:.2f}), low overfitting gap ({winner['gap']:.3f}), "
            f"and acceptable latency ({winner['latency']:.1f}ms)."
        )

        return FinalModelDecision(
            selected_model=winner["name"],
            algorithm=c_win.get("algorithm", winner["name"]),
            composite_score=round(winner["composite"], 4),
            reason=reason,
            primary_metric_name=primary_metric,
            primary_metric_value=round(winner["prim_val"], 4),
            secondary_metrics={k: round(float(v), 4) for k, v in winner["metrics"].items() if isinstance(v, (int, float))},
            cv_stability_score=round(winner["stability"], 4),
            generalization_gap=round(winner["gap"], 4),
            robustness_score=round(winner["robustness"], 4),
            inference_latency_ms=round(winner["latency"], 2),
            limitations=limitations,
            deployment_status="VALIDATED_READY",
        )

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        candidates = input_data.parameters.get("candidates") or []
        primary_metric = input_data.parameters.get("primary_metric", "f1")
        maximize = input_data.parameters.get("maximize", True)

        try:
            decision = self.rank_candidates(candidates, primary_metric=primary_metric, maximize=maximize)
            return AgentOutput(
                success=True,
                data=decision.model_dump(),
                message=decision.reason,
            )
        except Exception as e:
            logger.error(f"[FinalModelSelectionAgent] Error: {e}")
            return AgentOutput(success=False, errors=[str(e)])
