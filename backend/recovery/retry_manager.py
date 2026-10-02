"""
Retry Manager & Circuit Breakers
Enforces bounded retries, exponential backoff with jitter, loop prevention,
and service-level circuit breaking across LLMs, databases, MCP, and external APIs.
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Set, Tuple
from recovery.policies import (
    MAX_COST_BUDGET,
    MAX_RECOVERY_ATTEMPTS,
    MAX_RECOVERY_TIME_SECONDS,
    MAX_RETRIES,
    MAX_SAME_ERROR_ATTEMPTS,
    CircuitBreakerState,
    RecoveryDecisionState,
)


class CircuitBreaker:
    """Circuit breaker for an individual external service or provider."""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    def record_success(self) -> None:
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def can_execute(self) -> bool:
        if self.state == CircuitBreakerState.CLOSED:
            return True
        if self.state == CircuitBreakerState.OPEN:
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.cooldown_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        if self.state == CircuitBreakerState.HALF_OPEN:
            return True
        return False


class RetryManager:
    """Manages retry budgets, backoff delays, loop detection, and circuit breakers."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "gemini": CircuitBreaker("gemini"),
            "groq": CircuitBreaker("groq"),
            "cloudflare": CircuitBreaker("cloudflare"),
            "database": CircuitBreaker("database"),
            "mcp": CircuitBreaker("mcp"),
            "external_api": CircuitBreaker("external_api"),
        }
        # Tracks visited states: set of (workflow_id, node_or_agent, error_signature, strategy)
        self.visited_recovery_states: Set[str] = set()
        self.error_counts: Dict[str, int] = {}
        self.workflow_start_times: Dict[str, float] = {}
        self.workflow_costs: Dict[str, float] = {}

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        name_lower = service_name.lower()
        if name_lower not in self.circuit_breakers:
            self.circuit_breakers[name_lower] = CircuitBreaker(name_lower)
        return self.circuit_breakers[name_lower]

    def record_workflow_start(self, workflow_id: str) -> None:
        if workflow_id not in self.workflow_start_times:
            self.workflow_start_times[workflow_id] = time.time()
            self.workflow_costs[workflow_id] = 0.0

    def add_cost(self, workflow_id: str, cost: float) -> None:
        self.workflow_costs[workflow_id] = self.workflow_costs.get(workflow_id, 0.0) + cost

    def evaluate_retry_eligibility(
        self,
        workflow_id: str,
        agent_id: str,
        error_signature: str,
        strategy_name: str,
        attempt_count: int,
    ) -> Tuple[bool, RecoveryDecisionState, str]:
        """
        Determines if an operation may be retried or recovered under bounded policy.
        Returns (is_allowed, decision_state, reason).
        """
        self.record_workflow_start(workflow_id)

        # 1. Total attempt limit check
        if attempt_count > MAX_RECOVERY_ATTEMPTS:
            return (
                False,
                RecoveryDecisionState.UNRECOVERABLE,
                f"Exceeded maximum recovery attempts ({MAX_RECOVERY_ATTEMPTS}).",
            )

        # 2. Same error repetition limit
        err_key = f"{workflow_id}:{error_signature}"
        same_error_attempts = self.error_counts.get(err_key, 0) + 1
        self.error_counts[err_key] = same_error_attempts
        if same_error_attempts > MAX_SAME_ERROR_ATTEMPTS:
            return (
                False,
                RecoveryDecisionState.SAFE_STOP,
                f"Same error encountered {same_error_attempts} times; halting to prevent repeated cycles.",
            )

        # 3. Agent Loop Detection (Infinite loop prevention)
        state_key = f"{workflow_id}:{agent_id}:{error_signature}:{strategy_name}"
        if state_key in self.visited_recovery_states:
            return (
                False,
                RecoveryDecisionState.SAFE_STOP,
                f"Agent recovery loop detected: state '{strategy_name}' already attempted for this error.",
            )
        self.visited_recovery_states.add(state_key)

        # 4. Total recovery timeout check
        elapsed = time.time() - self.workflow_start_times.get(workflow_id, time.time())
        if elapsed > MAX_RECOVERY_TIME_SECONDS:
            return (
                False,
                RecoveryDecisionState.SAFE_STOP,
                f"Recovery time budget exceeded ({elapsed:.1f}s > {MAX_RECOVERY_TIME_SECONDS}s).",
            )

        # 5. Cost budget check
        cost = self.workflow_costs.get(workflow_id, 0.0)
        if cost > MAX_COST_BUDGET:
            return (
                False,
                RecoveryDecisionState.SAFE_STOP,
                f"Recovery cost budget exceeded (${cost:.2f} > ${MAX_COST_BUDGET}).",
            )

        return (True, RecoveryDecisionState.RETRY_REQUIRED, "Retry attempt within safety limits.")

    @classmethod
    def calculate_backoff(cls, attempt: int, base: float = 1.5, max_delay: float = 30.0) -> float:
        """Computes exponential backoff with randomized jitter."""
        exp_delay = base ** attempt
        jitter = random.uniform(0.1, 0.5)
        return min(exp_delay + jitter, max_delay)
