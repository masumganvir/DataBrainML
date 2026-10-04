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
    """Decode and validate signed JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        return None
