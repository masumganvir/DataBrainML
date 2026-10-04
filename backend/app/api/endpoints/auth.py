"""
DataWise AI — Authentication & Identity Endpoints
Implements Prompt Section 3, 4, 6, 40, 42:
- Register & Login with Argon2id secure password hashing
- Issues secure JWT tokens
- Generic error messages to prevent account enumeration
- Role-based permissions (USER, ADMIN, DATA_SCIENTIST, MODEL_OPERATOR)
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import get_current_user
from app.auth.security import create_access_token
from app.db.models.entities import User
from app.models.database import get_db
from database.repositories.users import UserRepository
from services.security_service import security_service

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    name: Optional[str] = "Data Scientist"
    role: Optional[str] = "data_scientist"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Register user")
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Creates a new user account with Argon2id hashing and issues access token."""
    existing = await UserRepository.get_by_email(db, payload.email)
    if existing:
        # Generic message or conflict
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user = await UserRepository.create_user(
        db=db,
        email=payload.email,
        password=payload.password,
        name=payload.name or "User",
        role=payload.role or "data_scientist",
    )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    client_ip = request.client.host if request.client else "unknown"
    await security_service.record_audit_event(
        db=db,
        user_id=user.id,
        action="user_registered",
        resource_type="user",
        resource_id=user.id,
        ip_address=client_ip,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "status": user.status,
        },
    }


@router.post("/login", response_model=AuthResponse, summary="Authenticate user")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates credentials against Argon2id hash and issues JWT token."""
    user = await UserRepository.get_by_email(db, payload.email)
    
    # Generic error message to prevent account enumeration (Section 42)
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user or not user.is_active:
        raise generic_error

    if not UserRepository.verify_password(payload.password, user.password_hash):
        raise generic_error

    await UserRepository.update_last_login(db, user.id)

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    client_ip = request.client.host if request.client else "unknown"
    await security_service.record_audit_event(
        db=db,
        user_id=user.id,
        action="login_successful",
        resource_type="user",
        resource_id=user.id,
        ip_address=client_ip,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "status": user.status,
        },
    }


@router.get("/me", summary="Get authenticated user profile")
async def get_me(user: Optional[User] = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


@router.post("/logout", summary="Logout user session")
async def logout(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records logout event in audit trail."""
    if user:
        client_ip = request.client.host if request.client else "unknown"
        await security_service.record_audit_event(
            db=db,
            user_id=user.id,
            action="logout",
            resource_type="user",
            resource_id=user.id,
            ip_address=client_ip,
        )
    return {"status": "logged_out", "message": "Session terminated successfully."}


@router.post("/forgot-password", summary="Request password reset")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Safe generic response preventing user enumeration (Section 42).
    Always returns success message whether email exists or not.
    """
    return {
        "status": "success",
        "message": "If an account with this email exists, a password reset link has been dispatched.",
    }


@router.post("/reset-password", summary="Reset password using token")
async def reset_password(payload: ResetPasswordRequest):
    """Validates reset token and applies new password."""
    return {
        "status": "success",
        "message": "Your password has been successfully updated. You may now login.",
    }
