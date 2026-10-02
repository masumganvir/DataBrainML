"""
DataWise AI — Chat & Workflow Orchestration Endpoints

Provides:
  - POST /sessions/{session_id}/chat        — Send a message to the AI agent
  - POST /sessions/{session_id}/workflow/run — Trigger the full analysis workflow
  - GET  /sessions/{session_id}/workflow/status — Get current workflow status
  - GET  /sessions/{session_id}/chat/history   — Conversation history
  - WebSocket /sessions/{session_id}/chat/stream — Streaming chat
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coordinator import multi_agent_coordinator
from app.graph.llm_provider import LLMMessage, llm_provider
from app.graph.workflow import run_analysis_workflow
from app.models.database import get_db
from app.models.db_models import ConversationMessage, Dataset, Session
from app.security.prompt_guard import prompt_guard
from app.state.data_science_state import DataScienceState
from app.tools.storage import storage_manager

router = APIRouter()

# ------------------------------------------------------------------ #
#  Schemas
# ------------------------------------------------------------------ #

class ChatRequest(BaseModel):
    message: str
    include_context: bool = True
    agent_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    role: str = "assistant"
    content: str
    stage: Optional[str] = None
    agent_name: Optional[str] = None
    agent_role: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    msg_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class WorkflowStatusResponse(BaseModel):
    session_id: str
    current_stage: str
    status: str
    completed_stages: List[str] = []
    has_pending_decision: bool = False
    ml_readiness_score: Optional[float] = None


# ------------------------------------------------------------------ #
#  Chat Endpoint
# ------------------------------------------------------------------ #

SYSTEM_PROMPT = """You are DataWise AI, a world-class AI data scientist and ML engineer.

You help users understand their data, fix data quality issues, engineer features,
select ML models, and build production-ready preprocessing pipelines.

Key behaviors:
- Always quantify findings (percentages, counts, correlations)
- Propose destructive operations before applying them
- Generate clean, runnable Python code when asked
- Use structured markdown: headers, bullet points, code blocks
- Flag risks with ⚠️ and strengths with ✅
- Be concise but thorough
"""


@router.post(
    "/{session_id}/chat",
    response_model=ChatResponse,
    summary="Send a message to the DataWise AI agent",
)
async def chat(
    session_id: str,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a user message and receive an AI response."""
    sess_q = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_q.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    # Validate user message against prompt injection
    assessment = prompt_guard.evaluate(payload.message)
    clean_message = assessment.sanitized_prompt

    # Persist user message
    user_msg = ConversationMessage(
        session_id=session_id,
        role="user",
        content=clean_message,
        msg_metadata={
            "stage": session.current_stage,
            "is_safe": assessment.is_safe,
            "risk_score": assessment.risk_score,
        },
    )
    db.add(user_msg)
    await db.commit()

    if not assessment.is_safe:
        warning_reply = (
            "⚠️ **Security Notice**: Your prompt triggered safety filters "
            f"({assessment.warning_message}). Please reformulate your request "
            "focusing on your dataset analysis, feature engineering, or modeling objectives."
        )
        assistant_msg = ConversationMessage(
            session_id=session_id,
            role="assistant",
            content=warning_reply,
            msg_metadata={"stage": session.current_stage, "security_blocked": True},
        )
        db.add(assistant_msg)
        await db.commit()
        return ChatResponse(session_id=session_id, content=warning_reply, stage=session.current_stage)

    # Load conversation history (last 20 messages)
    hist_q = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(20)
    )
    history = list(reversed(hist_q.scalars().all()))

    # Build dataset state for multi-agent reasoning
    ds_state: DataScienceState = {
        "session_id": session_id,
        "current_stage": session.current_stage,
        "target_column": session.target_column,
        "task_type": session.task_type,
    }
    if payload.include_context:
        ds_q = await db.execute(
            select(Dataset)
            .where(Dataset.session_id == session_id)
            .order_by(Dataset.created_at.desc())
        )
        dataset = ds_q.scalars().first()
        if dataset:
            ds_state["dataset_path_original"] = dataset.file_path
            ds_state["dataset_path_analysis"] = dataset.file_path
            ds_state["row_count_original"] = dataset.row_count
            ds_state["column_count_original"] = dataset.column_count
            if dataset.profile_summary:
                ds_state["column_profiles"] = dataset.profile_summary.get("columns", [])
                ds_state["numerical_columns"] = dataset.profile_summary.get("classification", {}).get("numerical", [])
                ds_state["categorical_columns"] = dataset.profile_summary.get("classification", {}).get("categorical", [])
            if dataset.quality_summary:
                ds_state["missing_value_report"] = dataset.quality_summary.get("missing_reports", [])
                ds_state["duplicate_report"] = dataset.quality_summary.get("duplicates", {})

    # Build messages history
    llm_messages = [
        LLMMessage(role=msg.role if msg.role in ("user", "assistant") else "user", content=msg.content)
        for msg in history[:-1]  # All except the last (just added user message)
    ]

    # Dispatch to the most qualified domain agent
    agent, response_text = await multi_agent_coordinator.dispatch_chat(
        query=clean_message,
        state=ds_state,
        history=llm_messages,
        forced_agent_id=payload.agent_id,
    )

    # Persist assistant message
    assistant_msg = ConversationMessage(
        session_id=session_id,
        role="assistant",
        content=response_text,
        msg_metadata={
            "stage": session.current_stage,
            "agent_name": agent.name,
            "agent_role": agent.role,
        },
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        session_id=session_id,
        role="assistant",
        content=response_text,
        stage=session.current_stage,
        agent_name=agent.name,
        agent_role=agent.role,
    )


# ------------------------------------------------------------------ #
#  Agent Registry Listing
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/agents",
    summary="List all specialized agents in the multi-agent system",
)
async def list_available_agents(session_id: str) -> List[Dict[str, str]]:
    """Return all specialized agents available to assist with data science tasks."""
    return multi_agent_coordinator.list_agents()


# ------------------------------------------------------------------ #
#  Conversation History
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/chat/history",
    response_model=List[MessageResponse],
    summary="Get conversation history for a session",
)
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> List[MessageResponse]:
    q = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at.asc())
        .limit(limit)
    )
    messages = q.scalars().all()
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat() if m.created_at else "",
            msg_metadata=m.msg_metadata,
        )
        for m in messages
    ]


# ------------------------------------------------------------------ #
#  Workflow Trigger
# ------------------------------------------------------------------ #

@router.post(
    "/{session_id}/workflow/run",
    summary="Trigger the full analysis workflow for a session",
)
async def run_workflow(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Run the complete DataWise AI analysis pipeline."""
    sess_q = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_q.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    ds_q = await db.execute(
        select(Dataset)
        .where(Dataset.session_id == session_id)
        .order_by(Dataset.created_at.desc())
    )
    dataset = ds_q.scalars().first()
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset uploaded for this session.")

    # Build initial state
    initial_state = {
        "session_id": session_id,
        "dataset_id": dataset.id,
        "dataset_path_original": dataset.file_path,
        "dataset_path_analysis": dataset.file_path,
        "dataset_metadata": {
            "filename": dataset.original_filename,
            "format": dataset.file_format,
            "rows": dataset.row_count,
            "columns": dataset.column_count,
        },
        "target_column": session.target_column,
        "task_type": session.task_type,
        "current_stage": "PROFILE",
        "completed_stages": [],
        "errors": [],
        "should_continue": True,
        "user_decisions": [],
        "conversation_history": [],
        "total_llm_calls": 0,
        "total_tokens_used": 0,
    }

    # Update session status
    session.status = "active"
    session.current_stage = "PROFILE"
    await db.commit()

    # Run workflow asynchronously
    try:
        final_state = await run_analysis_workflow(initial_state)

        # Update session stage from final state
        session.current_stage = final_state.get("current_stage", "COMPLETE")
        session.status = "completed" if final_state.get("current_stage") == "COMPLETE" else "active"
        await db.commit()

        # Persist the LLM interpretation as a message if present
        llm_history = final_state.get("conversation_history", [])
        for msg in llm_history:
            conv_msg = ConversationMessage(
                session_id=session_id,
                role=msg.get("role", "assistant"),
                content=msg.get("content", ""),
                msg_metadata={"stage": final_state.get("current_stage"), "source": "workflow"},
            )
            db.add(conv_msg)
        await db.commit()

        return {
            "session_id": session_id,
            "status": "completed" if final_state.get("current_stage") == "COMPLETE" else "paused",
            "current_stage": final_state.get("current_stage"),
            "completed_stages": final_state.get("completed_stages", []),
            "has_pending_decision": bool(final_state.get("pending_decision")),
            "pending_decision": final_state.get("pending_decision"),
            "ml_readiness_score": final_state.get("ml_readiness_score"),
            "ml_readiness_level": final_state.get("ml_readiness_level"),
            "errors": final_state.get("errors", []),
        }
    except Exception as exc:  # noqa: BLE001
        session.status = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc


# ------------------------------------------------------------------ #
#  Workflow Status
# ------------------------------------------------------------------ #

@router.get(
    "/{session_id}/workflow/status",
    response_model=WorkflowStatusResponse,
    summary="Get current workflow stage and status",
)
async def get_workflow_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> WorkflowStatusResponse:
    sess_q = await db.execute(select(Session).where(Session.id == session_id))
    session = sess_q.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return WorkflowStatusResponse(
        session_id=session_id,
        current_stage=session.current_stage or "INGEST",
        status=session.status or "created",
        completed_stages=[],
        has_pending_decision=False,
    )


# ------------------------------------------------------------------ #
#  WebSocket Streaming Chat
# ------------------------------------------------------------------ #

@router.websocket("/{session_id}/chat/stream")
async def chat_stream(
    session_id: str,
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint for streaming AI chat responses."""
    await websocket.accept()

    try:
        while True:
            user_message = await websocket.receive_text()

            sess_q = await db.execute(select(Session).where(Session.id == session_id))
            session = sess_q.scalar_one_or_none()
            if not session:
                await websocket.send_text("[ERROR] Session not found.")
                break

            messages = [LLMMessage(role="user", content=user_message)]

            # Stream response
            full_response = ""
            async for chunk in llm_provider.stream(
                messages=messages,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.4,
                max_tokens=2000,
            ):
                await websocket.send_text(chunk)
                full_response += chunk

            # Signal end of stream
            await websocket.send_text("[DONE]")

            # Persist messages
            user_msg = ConversationMessage(session_id=session_id, role="user", content=user_message)
            asst_msg = ConversationMessage(session_id=session_id, role="assistant", content=full_response)
            db.add(user_msg)
            db.add(asst_msg)
            await db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        try:
            await websocket.send_text(f"[ERROR] {exc}")
        except Exception:  # noqa: BLE001
            pass
