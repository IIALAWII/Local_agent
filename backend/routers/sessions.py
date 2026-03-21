"""Sessions router – GET /api/sessions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from memory_short import session_store

router = APIRouter(prefix="/api", tags=["sessions"])


class SessionInfo(BaseModel):
    """Metadata for a single chat session."""

    session_id: str
    message_count: int


class SessionList(BaseModel):
    """Response body listing all active sessions."""

    sessions: list[SessionInfo]


@router.get("/sessions", response_model=SessionList)
async def list_sessions() -> SessionList:
    """Return all currently active chat sessions.

    Returns:
        A :class:`SessionList` containing every session ID and its message count.
    """
    sessions = [
        SessionInfo(
            session_id=sid,
            message_count=session_store.get_or_create(sid).message_count(),
        )
        for sid in session_store.list_sessions()
    ]
    return SessionList(sessions=sessions)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str) -> None:
    """Delete a chat session and its associated short-term memory.

    Args:
        session_id: The session ID to remove.
    """
    session_store.delete(session_id)
