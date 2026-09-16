"""
Session management endpoints for creating, listing, and retrieving conversations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.repositories import SessionRepository
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class SessionCreate(BaseModel):
    """Request model for creating a new session."""
    title: Optional[str] = Field(None, max_length=255, description="Optional session title")
    model_provider: Optional[str] = Field(None, description="LLM provider to use (anthropic, openai, ollama)")
    model_name: Optional[str] = Field(None, description="Specific model name")


class SessionResponse(BaseModel):
    """Response model for a session."""
    session_id: UUID
    created_at: datetime
    updated_at: datetime
    title: Optional[str]
    model_provider: str
    model_name: str
    message_count: Optional[int] = None
    is_active: bool = True


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreate,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation session.
    
    Args:
        request: Session creation parameters
        settings: Application settings
        db: Database session
    
    Returns:
        Created session details
    """
    # Use provided model or fall back to settings
    model_provider = request.model_provider or settings.llm_provider
    
    if model_provider == "anthropic":
        model_name = request.model_name or settings.anthropic_model
    elif model_provider == "openai":
        model_name = request.model_name or settings.openai_model
    else:  # ollama
        model_name = request.model_name or settings.ollama_model
    
    # Create session using repository
    repo = SessionRepository(db)
    session = repo.create(
        title=request.title or "New Conversation",
        model_provider=model_provider,
        model_name=model_name
    )
    
    return SessionResponse(
        session_id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        title=session.title,
        model_provider=session.model_provider,
        model_name=session.model_name,
        message_count=0,
        is_active=session.is_active
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List all sessions with pagination.
    
    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip for pagination
        is_active: Optional filter for active/archived sessions
        db: Database session
    
    Returns:
        List of sessions with pagination metadata
    """
    repo = SessionRepository(db)
    sessions, total = repo.list(limit=limit, offset=offset, is_active=is_active)
    
    session_responses = []
    for session in sessions:
        message_count = repo.get_message_count(session.id)
        session_responses.append(
            SessionResponse(
                session_id=session.id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                title=session.title,
                model_provider=session.model_provider,
                model_name=session.model_name,
                message_count=message_count,
                is_active=session.is_active
            )
        )
    
    return SessionListResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: UUID of the session to retrieve
        db: Database session
    
    Returns:
        Session details including message history
    
    Raises:
        HTTPException: If session not found
    """
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id, include_messages=True)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message_count = len(session.messages) if session.messages else 0
    
    return SessionResponse(
        session_id=session.id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        title=session.title,
        model_provider=session.model_provider,
        model_name=session.model_name,
        message_count=message_count,
        is_active=session.is_active
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Soft-delete a session (set is_active = false).
    
    Args:
        session_id: UUID of the session to delete
        db: Database session
    
    Raises:
        HTTPException: If session not found
    """
    repo = SessionRepository(db)
    success = repo.soft_delete(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return None
