"""
DataWise AI — Logging Configuration

Uses loguru for structured, colored, level-filtered logging.
In production: JSON format to stdout for log aggregators.
In development: colored human-readable format.
"""

from __future__ import annotations

import sys
from loguru import logger
from app.config.settings import get_settings


def setup_logging() -> None:
    """Configure loguru logger based on environment settings."""
    settings = get_settings()
    logger.remove()  # remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.app_log_level,
        colorize=settings.is_development,
        serialize=settings.is_production,  # JSON in production
    )

    # File logging
    logger.add(
        "logs/datawise_{time:YYYY-MM-DD}.log",
        rotation="00:00",       # rotate daily
        retention="30 days",
        level=settings.app_log_level,
        serialize=True,         # always JSON in files
        enqueue=True,           # async-safe
    )

    logger.info(f"Logging initialized [level={settings.app_log_level}, env={settings.app_env}]")
