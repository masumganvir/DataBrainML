"""
DataWise AI — LLM Exponential Backoff & Retry Logic
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable, TypeVar
from loguru import logger

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 2,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> T:
    """Executes a synchronous function with exponential backoff and jitter."""
    delay = initial_delay
    last_error: Exception = Exception("Unknown execution failure")

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                logger.warning(f"[Retry] Max retries ({max_retries}) exhausted: {exc}")
                raise

            sleep_time = delay + (random.uniform(0, 0.2 * delay) if jitter else 0)
            logger.debug(f"[Retry] Attempt {attempt + 1} failed ({exc}). Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor

    raise last_error


async def aretry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 2,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
) -> Any:
    """Executes an asynchronous coroutine with exponential backoff and jitter."""
    delay = initial_delay
    last_error: Exception = Exception("Unknown execution failure")

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                logger.warning(f"[AsyncRetry] Max retries ({max_retries}) exhausted: {exc}")
                raise

            sleep_time = delay + (random.uniform(0, 0.2 * delay) if jitter else 0)
            logger.debug(f"[AsyncRetry] Attempt {attempt + 1} failed ({exc}). Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor

    raise last_error
