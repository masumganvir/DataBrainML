"""
DataWise AI — Human Decisions API Endpoints

Manages human-in-the-loop decisions, approval flows, and audit logs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.governance import HumanApprovalNode
from app.models.database import get_db
from app.models.db_models import Dataset, Session, UserDecision
from app.tools.storage import storage_manager

router = APIRouter()


# ------------------------------------------------------------------ #
#  Schemas
# ------------------------------------------------------------------ #

class DecisionOption(BaseModel):
    value: str
    label: str


class PendingDecisionResponse(BaseModel):
    decision_id: str
    stage: str
    category: str
    title: str
    message: str
    recommended_choice: str
    options: List[DecisionOption]
    context: Optional[Dict[str, Any]] = None


class SubmitDecisionRequest(BaseModel):
    decision_key: str = Field(..., description="Unique key for the decision, e.g. drop_column_total_charges")
    decision_value: str = Field(..., description="Selected choice, e.g. approve_drop or custom string")
    stage: str = Field("HUMAN_APPROVAL", description="Workflow stage when decision was made")
    context: Optional[Dict[str, Any]] = None


class UserDecisionResponse(BaseModel):
    id: str
    session_id: str
    stage: str
    decision_key: str
    decision_value: str
    context: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
#  Endpoints
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/decisions/pending",
    response_model=Optional[PendingDecisionResponse],
    summary="Get the currently active decision awaiting human approval",
)
async def get_pending_decision(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates current session state to detect if any destructive operation
    requires human verification before automated pipeline progression.
    """
    session_query = await db.execute(select(Session).where(Session.id == session_id))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # Fetch latest dataset for session
    ds_query = await db.execute(
        select(Dataset).where(Dataset.session_id == session_id).order_by(Dataset.created_at.desc())
    )
    dataset = ds_query.scalars().first()
    if not dataset:
        return None

    # Fetch existing decisions
    dec_query = await db.execute(
        select(UserDecision).where(UserDecision.session_id == session_id)
    )
    decisions = dec_query.scalars().all()
    user_decisions = [
        {"decision_key": d.decision_key, "decision_value": d.decision_value}
        for d in decisions
    ]

    # Reconstruct state from cached summaries
    state_mock = {
        "user_decisions": user_decisions,
        "missing_value_report": dataset.quality_summary.get("missing_reports", []) if dataset.quality_summary else [],
        "duplicate_report": dataset.quality_summary.get("duplicates", {}) if dataset.quality_summary else {},
    }

    pending = HumanApprovalNode.inspect_proposed_actions(state_mock)  # type: ignore
    if not pending:
        return None

    return PendingDecisionResponse(
        decision_id=pending["decision_id"],
        stage=pending["stage"],
        category=pending["category"],
        title=pending["title"],
        message=pending["message"],
        recommended_choice=pending["recommended_choice"],
        options=[DecisionOption(**opt) for opt in pending["options"]],
        context=pending.get("context"),
    )


@router.post(
    "/{session_id}/decisions",
    response_model=UserDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit human decision or approval override",
)
async def submit_user_decision(
    session_id: str,
    payload: SubmitDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Records human approval or rejection in the audit trail and advances the workflow.
    """
    session_query = await db.execute(select(Session).where(Session.id == session_id))
    session = session_query.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    decision = UserDecision(
        session_id=session_id,
        stage=payload.stage,
        decision_key=payload.decision_key,
        decision_value=payload.decision_value,
        context=payload.context,
    )
    db.add(decision)

    # Resume workflow stage
    session.current_stage = "FEATURE_ENGINEERING"
    await db.commit()
    await db.refresh(decision)

    return UserDecisionResponse(
        id=decision.id,
        session_id=decision.session_id,
        stage=decision.stage,
        decision_key=decision.decision_key,
        decision_value=decision.decision_value,
        context=decision.context,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
    )


@router.get(
    "/{session_id}/decisions",
    response_model=List[UserDecisionResponse],
    summary="List all recorded decisions for a session",
)
async def list_user_decisions(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    dec_query = await db.execute(
        select(UserDecision)
        .where(UserDecision.session_id == session_id)
        .order_by(UserDecision.created_at.asc())
    )
    decisions = dec_query.scalars().all()

    return [
        UserDecisionResponse(
            id=d.id,
            session_id=d.session_id,
            stage=d.stage,
            decision_key=d.decision_key,
            decision_value=d.decision_value,
            context=d.context,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in decisions
    ]
