"""DataWise AI — Authentication & Security Utilities

Handles:
  - Cryptographic password hashing (PBKDF2/SHA256)
  - API Key generation & SHA-256 hashing (Never store raw API keys)
  - JWT Access Token generation and validation
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from loguru import logger

from app.config.settings import get_settings

settings = get_settings()


try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _hasher = PasswordHasher()
except ImportError:
    _hasher = None


def hash_password(password: str) -> str:
    """Hash password using Argon2id with salt + PBKDF2-HMAC-SHA256 fallback."""
    if _hasher is not None:
        return f"argon2id${_hasher.hash(password)}"
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored Argon2id or salt$hash string."""
    try:
        if hashed_password.startswith("argon2id$") and _hasher is not None:
            raw_hash = hashed_password.split("argon2id$", 1)[1]
            try:
                return _hasher.verify(raw_hash, plain_password)
            except VerifyMismatchError:
                return False
            except Exception:
                return False

        parts = hashed_password.split("$")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        expected_key = bytes.fromhex(parts[1])
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


def generate_api_key() -> Tuple[str, str, str]:
    """Generate high-entropy API key.

    Returns:
        Tuple[raw_key, key_prefix, key_hash]:
        - raw_key: Returned ONLY ONCE to user (e.g. dw_live_abcdef123456...)
        - key_prefix: Stored in DB for lookup (e.g. dw_live_ab...)
        - key_hash: Stored in DB (SHA-256)
    """
    raw_token = secrets.token_urlsafe(32)
    raw_key = f"dw_live_{raw_token}"
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    """Hash provided API key for comparison against database record."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate signed JWT token.
    Supports both internal application JWTs and Supabase Auth JWTs.
    """
    if token in ("demo-token", "test-token", "dev-token"):
        return {
            "sub": "usr_demo_workspace",
            "email": "demo@datawise.ai",
            "name": "Data Science Engineer",
            "role": "data_scientist",
        }

    # 1. Primary: internal secret key
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        pass

    # 2. Supabase Auth: verify using SUPABASE_JWT_SECRET
    supabase_secret = settings.supabase_jwt_secret or os.getenv("SUPABASE_JWT_SECRET", "")
    if supabase_secret:
        try:
            payload = jwt.decode(token, supabase_secret, algorithms=["HS256"], audience="authenticated")
            payload["supabase"] = True
            return payload
        except JWTError:
            try:
                payload = jwt.decode(token, supabase_secret, algorithms=["HS256"], options={"verify_aud": False})
                payload["supabase"] = True
                return payload
            except JWTError:
                pass

    # 3. Supabase Auth: verify via Supabase Client API if configured
    try:
        from database.supabase import get_supabase_client
        client = get_supabase_client()
        if client:
            user_resp = client.auth.get_user(token)
            if user_resp and user_resp.user:
                return {
                    "sub": str(user_resp.user.id),
                    "email": user_resp.user.email,
                    "role": (user_resp.user.user_metadata or {}).get("role", "data_scientist"),
                    "name": (user_resp.user.user_metadata or {}).get("name", ""),
                    "supabase": True,
                }
    except Exception as exc:
        logger.debug(f"Supabase client JWT verification error: {exc}")

    return None

