"""
DataWise AI — User Repository
Handles user lifecycle, authentication, profile updates, and Argon2id password hashing.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ph = PasswordHasher()
except ImportError:
    _ph = None

from app.auth.security import hash_password as pbkdf2_hash, verify_password as pbkdf2_verify
from app.db.models.entities import User


class UserRepository:
    """Manages user persistence, password verification, and authentication lookup."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes password using Argon2id with automatic PBKDF2 fallback."""
        if _ph is not None:
            return f"argon2id${_ph.hash(password)}"
        return pbkdf2_hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies plaintext against Argon2id or legacy PBKDF2 hashes."""
        if hashed_password.startswith("argon2id$") and _ph is not None:
            raw_hash = hashed_password.split("argon2id$", 1)[1]
            try:
                return _ph.verify(raw_hash, plain_password)
            except VerifyMismatchError:
                return False
            except Exception:
                return False
        return pbkdf2_verify(plain_password, hashed_password)

    @classmethod
    async def create_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        name: str = "",
        role: str = "data_scientist",
    ) -> User:
        """Creates a new user with secure password hash."""
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        hashed = cls.hash_password(password)
        user = User(
            id=user_id,
            email=email.strip().lower(),
            name=name.strip() or email.split("@")[0],
            password_hash=hashed,
            role=role,
            status="active",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"[UserRepository] Created user {user.id} ({user.email}) with role '{role}'")
        return user

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional[User]:
        """Look up user by email."""
        stmt = select(User).where(User.email == email.strip().lower())
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: str) -> Optional[User]:
        """Look up user by unique ID."""
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def update_last_login(cls, db: AsyncSession, user_id: str) -> None:
        """Updates timestamp of user's last successful authentication."""
        try:
            from datetime import datetime
            stmt = update(User).where(User.id == user_id).values(last_login_at=datetime.utcnow())
            await db.execute(stmt)
            await db.commit()
        except Exception as exc:
            logger.warning(f"Could not update last login for {user_id}: {exc}")
