"""
DataWise AI — Supabase Database & Client Integration
Provides connection management for Supabase PostgreSQL (via SQLAlchemy async engine)
and Supabase Client (Auth, Storage, PostgREST API).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from loguru import logger

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any

from app.config.settings import get_settings

settings = get_settings()

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns singleton instance of Supabase Client using public anon key.
    Enforces Row Level Security (RLS) on client queries.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

    if not supabase_url or not supabase_key:
        logger.debug("[Supabase] SUPABASE_URL or SUPABASE_KEY not configured. Running in hybrid/direct DB mode.")
        return None

    if create_client is None:
        logger.warning("[Supabase] supabase-py library not available.")
        return None

    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info(f"[Supabase] Connected to Supabase project at {supabase_url}")
        return _supabase_client
    except Exception as exc:
        logger.error(f"[Supabase] Initialization error: {exc}")
        return None


def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns administrative Supabase Client using Service Role Key.
    Used exclusively by backend workers and admin background processes.
    """
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    supabase_url = os.getenv("SUPABASE_URL", "")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url or not service_role_key:
        return None

    if create_client is None:
        return None

    try:
        _supabase_admin_client = create_client(supabase_url, service_role_key)
        logger.info("[Supabase] Admin service role client initialized successfully.")
        return _supabase_admin_client
    except Exception as exc:
        logger.error(f"[Supabase] Admin client initialization error: {exc}")
        return None


def is_supabase_enabled() -> bool:
    """Checks if Supabase credentials are configured in the environment."""
    return bool(os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")))
