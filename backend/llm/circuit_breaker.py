"""
DataWise AI — LLM Circuit Breaker
Protects LLM providers by transitioning through CLOSED -> OPEN -> HALF_OPEN states
to avoid overwhelming failing or rate-limited upstream AI services.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, Optional
from loguru import logger


class CircuitState(str, Enum):
    CLOSED = "CLOSED"         # Normal operation: requests pass through
    OPEN = "OPEN"             # Provider is failing: requests fail fast
    HALF_OPEN = "HALF_OPEN"   # Testing recovery: probe request allowed


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
        half_open_success_threshold: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.consecutive_successes: int = 0
        self.last_failure_time: float = 0.0
        self.last_state_change: float = time.time()

    def allow_request(self) -> bool:
        """Determines whether a call to the provider is permitted."""
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if cooldown has elapsed
            if now - self.last_failure_time >= self.cooldown_seconds:
                logger.info(f"[CircuitBreaker:{self.name}] Cooldown elapsed. Transitioning OPEN -> HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.consecutive_successes = 0
                self.last_state_change = now
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited probe request
            return True

        return False

    def record_success(self) -> None:
        """Records a successful LLM invocation."""
        if self.state == CircuitState.HALF_OPEN:
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.half_open_success_threshold:
                logger.info(f"[CircuitBreaker:{self.name}] Probe successful. Transitioning HALF_OPEN -> CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.consecutive_successes = 0
                self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self, error: Optional[str] = None) -> None:
        """Records an error or rate limit rejection."""
        now = time.time()
        self.last_failure_time = now
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"[CircuitBreaker:{self.name}] Probe failed: {error}. Transitioning HALF_OPEN -> OPEN")
            self.state = CircuitState.OPEN
            self.last_state_change = now
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"[CircuitBreaker:{self.name}] Failure threshold ({self.failure_threshold}) exceeded: {error}. "
                    f"Transitioning CLOSED -> OPEN (cooldown: {self.cooldown_seconds}s)"
                )
                self.state = CircuitState.OPEN
                self.last_state_change = now


class CircuitBreakerRegistry:
    """Registry maintaining circuit breaker instances per provider."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        provider_name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 60.0,
    ) -> CircuitBreaker:
        name = provider_name.lower()
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                cooldown_seconds=cooldown_seconds,
            )
        return self._breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "state": b.state.value,
                "failure_count": b.failure_count,
                "last_failure_time": b.last_failure_time,
                "cooldown_seconds": b.cooldown_seconds,
            }
            for name, b in self._breakers.items()
        }


circuit_registry = CircuitBreakerRegistry()
