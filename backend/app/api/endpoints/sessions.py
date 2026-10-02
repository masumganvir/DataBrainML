"""
DataWise AI — Sessions Endpoint

CRUD for analysis sessions.
Each session ties together a dataset upload, the analysis workflow,
conversation history, and all generated artifacts.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.db_models import Session as DBSession

router = APIRouter()


# ------------------------------------------------------------------ #
#  Pydantic Schemas
# ------------------------------------------------------------------ #

class SessionCreate(BaseModel):
    name: str = "Untitled Session"


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    name: str
    status: str
    current_stage: str
    task_type: Optional[str]
    target_column: Optional[str]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        # Convert datetime to ISO strings
        if hasattr(self, '__dict__'):
            for field in ['created_at', 'updated_at']:
                val = getattr(self, field, None)
                if val and not isinstance(val, str):
                    object.__setattr__(self, field, val.isoformat())


# ------------------------------------------------------------------ #
#  Routes
# ------------------------------------------------------------------ #

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new analysis session."""
    session = DBSession(
        id=str(uuid.uuid4()),
        name=payload.name,
        status="created",
        current_stage="INGEST",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _to_response(session)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
):
    """List all sessions (most recent first)."""
    result = await db.execute(
        select(DBSession).order_by(DBSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [_to_response(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single session by ID."""
    session = await _get_session_or_404(session_id, db)
    return _to_response(session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update session name or status."""
    session = await _get_session_or_404(session_id, db)
    if payload.name is not None:
        session.name = payload.name
    if payload.status is not None:
        session.status = payload.status
    await db.commit()
    await db.refresh(session)
    return _to_response(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its associated data."""
    session = await _get_session_or_404(session_id, db)
    await db.delete(session)
    await db.commit()


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

async def _get_session_or_404(session_id: str, db: AsyncSession) -> DBSession:
    result = await db.execute(select(DBSession).where(DBSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return session


def _to_response(session: DBSession) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        name=session.name,
        status=session.status,
        current_stage=session.current_stage,
        task_type=session.task_type,
        target_column=session.target_column,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
    )
