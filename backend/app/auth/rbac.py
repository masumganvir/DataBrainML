"""DataWise AI — Role-Based Access Control (RBAC) & Dependencies

Roles:
  - owner: full administrative access
  - admin: project and user management
  - developer: workflow execution, code and model access
  - data_scientist: dataset exploration, training, tuning, evaluation
  - viewer: read-only access to datasets, reports, metrics

Permissions:
  - dataset.read, dataset.write
  - experiment.run
  - model.read, model.train, model.promote
  - deployment.create, deployment.manage
  - audit.read
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.db.models.entities import User
from app.db.session import get_db

security_scheme = HTTPBearer(auto_error=False)

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "dataset.read", "dataset.write", "experiment.run",
        "model.read", "model.train", "model.promote",
        "deployment.create", "deployment.manage", "audit.read", "admin.manage",
    },
    "admin": {
        "dataset.read", "dataset.write", "experiment.run",
        "model.read", "model.train", "model.promote",
        "deployment.create", "deployment.manage", "audit.read",
    },
    "developer": {
        "dataset.read", "dataset.write", "experiment.run",
        "model.read", "model.train", "deployment.create",
    },
    "data_scientist": {
        "dataset.read", "dataset.write", "experiment.run",
        "model.read", "model.train", "model.promote",
    },
    "viewer": {
        "dataset.read", "model.read",
    },
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieve authenticated user from JWT bearer token."""
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
        )

    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or deactivated.",
        )

    return user


def require_permission(required_perm: str):
    """Dependency factory enforcing granular RBAC permissions."""
    async def permission_checker(user: Optional[User] = Depends(get_current_user)) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for this operation.",
            )

        user_role = user.role or "viewer"
        granted_perms = ROLE_PERMISSIONS.get(user_role, set())

        if required_perm not in granted_perms and "admin.manage" not in granted_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Missing required permission: '{required_perm}'.",
            )

        return user

    return permission_checker
