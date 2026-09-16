"""
Message handling endpoints for sending and receiving chat messages.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.repositories import MessageRepository, SessionRepository
from app.agent.agent import Agent
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Request/Response Models
class MessageCreate(BaseModel):
    """Request model for sending a message."""
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    stream: bool = Field(False, description="Enable streaming response")


class SourceReference(BaseModel):
    """Source citation for grounded answers."""
    transcript_id: UUID
    episode_number: Optional[int]
    guest_name: Optional[str]
    title: str
    excerpt: str
    relevance_score: float


class ArtifactMetadata(BaseModel):
    """Metadata for generated artifacts."""
    artifact_id: UUID
    artifact_type: str  # "markdown", "html", "json"
    title: str
    word_count: Optional[int]


class MessageMetadata(BaseModel):
    """Metadata attached to assistant messages."""
    sources: list[SourceReference] = []
    artifacts: list[ArtifactMetadata] = []
    token_count: Optional[int] = None
    processing_time_ms: Optional[float] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    message_id: UUID
    role: str  # "user", "assistant", "system"
    content: str
    created_at: datetime
    metadata: Optional[MessageMetadata] = None


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    request: MessageCreate,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
):
    """
    Send a message to a session and receive assistant response.
    
    This endpoint orchestrates the full RAG pipeline:
    1. Store user message
    2. Retrieve relevant context from transcripts
    3. Generate response using agent
    4. Store assistant message
    5. Return response with sources
    
    Args:
        session_id: UUID of the session
        request: Message content and options
        settings: Application settings
        db: Database session
    
    Returns:
        Assistant's response with metadata
    
    Raises:
        HTTPException: If session not found or processing fails
    """
    import time
    start_time = time.time()
    
    logger.info(
        "processing_message",
        session_id=str(session_id),
        content_length=len(request.content),
        stream=request.stream
    )
    
    # Validate session exists
    session_repo = SessionRepository(db)
    session = session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store user message
    message_repo = MessageRepository(db)
    user_message = message_repo.create(
        session_id=session_id,
        role="user",
        content=request.content
    )
    
    # Process with agent
    try:
        agent = Agent(db)
        agent_response = agent.process_query(
            query=request.content,
            session_id=str(session_id),
            stream=request.stream
        )
        
        # Format sources for metadata
        sources_metadata = [
            {
                "transcript_id": str(source.transcript_id),
                "episode_number": source.episode_number,
                "guest_name": source.guest_name,
                "title": source.title,
                "excerpt": source.content[:200],
                "relevance_score": source.score
            }
            for source in agent_response.sources
        ]
        
        # Store assistant message
        assistant_message = message_repo.create(
            session_id=session_id,
            role="assistant",
            content=agent_response.content,
            token_count=agent_response.token_usage.get("output_tokens") if agent_response.token_usage else None,
            metadata={
                "sources": sources_metadata,
                "skill_used": agent_response.skill_used,
                "token_usage": agent_response.token_usage,
                **(agent_response.metadata or {})
            }
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update session timestamp
        session_repo.update(session_id, metadata=session.metadata)
        
        # Convert sources to response format
        source_responses = [
            SourceReference(
                transcript_id=source.transcript_id,
                episode_number=source.episode_number,
                guest_name=source.guest_name,
                title=source.title,
                excerpt=source.content[:200],
                relevance_score=source.score
            )
            for source in agent_response.sources
        ]
        
        return MessageResponse(
            message_id=assistant_message.id,
            role="assistant",
            content=assistant_message.content,
            created_at=assistant_message.created_at,
            metadata=MessageMetadata(
                sources=source_responses,
                artifacts=[],
                token_count=assistant_message.token_count,
                processing_time_ms=processing_time
            )
        )
        
    except Exception as e:
        logger.error("message_processing_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: UUID,
    limit: int = 50,
    offset: int = 0
):
    """
    Get message history for a session.
    
    Args:
        session_id: UUID of the session
        limit: Maximum number of messages to return
        offset: Number of messages to skip
    
    Returns:
        List of messages in chronological order
    """
    logger.info(
        "getting_messages",
        session_id=str(session_id),
        limit=limit,
        offset=offset
    )
    
    # TODO: Implement database query
    return {"messages": [], "total": 0}
