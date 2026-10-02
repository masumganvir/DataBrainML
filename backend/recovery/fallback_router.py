"""
Fallback Router
Orchestrates prioritized fallback cascades across algorithms, LLM providers,
preprocessing strategies, database connections, and specialized fallback agents.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from loguru import logger

from recovery.policies import RecoveryDecisionState
from recovery.retry_manager import CircuitBreaker


class LLMProviderNode:
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.total_calls: int = 0
        self.successful_calls: int = 0
        self.failed_calls: int = 0
        self.last_latency: float = 0.0
        self.circuit_breaker = CircuitBreaker(name, failure_threshold=2, cooldown_seconds=60.0)

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls


class FallbackRouter:
    """Manages fallback hierarchies prioritizing deterministic and validated paths."""

    # Model Candidate Fallback Cascade
    MODEL_FALLBACK_CASCADE = {
        "catboost": ["xgboost", "lightgbm", "hist_gradient_boosting", "random_forest", "logistic_regression"],
        "xgboost": ["lightgbm", "hist_gradient_boosting", "random_forest", "decision_tree"],
        "lightgbm": ["hist_gradient_boosting", "random_forest", "ridge"],
        "random_forest": ["hist_gradient_boosting", "extra_trees", "linear_model"],
    }

    def __init__(self):
        self.llm_providers: List[LLMProviderNode] = [
            LLMProviderNode("gemini", priority=1),
            LLMProviderNode("groq", priority=2),
            LLMProviderNode("cloudflare", priority=3),
            LLMProviderNode("deterministic", priority=4),
        ]

    def get_active_llm_provider(self) -> str:
        """Selects the highest-priority healthy LLM provider."""
        for node in sorted(self.llm_providers, key=lambda n: n.priority):
            if node.name == "deterministic" or node.circuit_breaker.can_execute():
                return node.name
        return "deterministic"

    def record_llm_result(self, provider_name: str, success: bool, latency: float = 0.0) -> None:
        for node in self.llm_providers:
            if node.name == provider_name:
                node.total_calls += 1
                node.last_latency = latency
                if success:
                    node.successful_calls += 1
                    node.circuit_breaker.record_success()
                else:
                    node.failed_calls += 1
                    node.circuit_breaker.record_failure()
                break

    def get_model_fallback(self, failed_model: str) -> Optional[str]:
        """Provides the next compatible model candidate."""
        key = failed_model.lower().strip()
        candidates = self.MODEL_FALLBACK_CASCADE.get(key, ["hist_gradient_boosting", "random_forest"])
        return candidates[0] if candidates else "hist_gradient_boosting"

    @classmethod
    def execute_with_fallback(
        cls,
        primary_callable: Callable[[], Any],
        fallback_callable: Callable[[], Any],
        fallback_name: str = "fallback",
    ) -> Tuple[Any, RecoveryDecisionState, str]:
        """
        Executes primary callable; on failure, switches safely to fallback callable.
        """
        try:
            res = primary_callable()
            return (res, RecoveryDecisionState.RECOVERED, "Primary execution succeeded.")
        except Exception as exc:
            logger.warning(f"Primary action failed ({exc}); switching to fallback: {fallback_name}")
            try:
                res_fallback = fallback_callable()
                return (
                    res_fallback,
                    RecoveryDecisionState.FALLBACK_USED,
                    f"Recovered successfully using fallback strategy: {fallback_name}",
                )
            except Exception as fb_exc:
                logger.error(f"Fallback action {fallback_name} also failed: {fb_exc}")
                return (
                    None,
                    RecoveryDecisionState.UNRECOVERABLE,
                    f"Both primary and fallback ({fallback_name}) failed: {fb_exc}",
                )
