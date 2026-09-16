"""
SQLAlchemy ORM models for the Lenny Growth Assistant.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, 
    String, Text, Float, ARRAY, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class Session(Base):
    """
    Conversation session model.
    Each session represents an independent conversation context.
    """
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    title = Column(String(255), nullable=True)
    model_provider = Column(String(50), nullable=False)  # 'anthropic', 'openai', 'ollama'
    model_name = Column(String(100), nullable=False)
    metadata = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title})>"


class Message(Base):
    """
    Individual message within a session.
    Stores both user and assistant messages.
    """
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    metadata = Column(JSONB, nullable=False, default=dict)  # sources, artifacts, tool_calls
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="valid_role"),
        Index("idx_messages_session_created", "session_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


class Transcript(Base):
    """
    Lenny's Podcast episode metadata and full text.
    """
    __tablename__ = "transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_number = Column(Integer, unique=True, nullable=True, index=True)
    title = Column(String(500), nullable=False)
    guest_name = Column(String(200), nullable=True, index=True)
    publish_date = Column(DateTime, nullable=True, index=True)
    duration_minutes = Column(Integer, nullable=True)
    full_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    topics = Column(ARRAY(Text), nullable=True)  # Array of topic tags
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunks = relationship("TranscriptChunk", back_populates="transcript", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_transcripts_topics", "topics", postgresql_using="gin"),
    )
    
    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, episode={self.episode_number}, guest={self.guest_name})>"


class TranscriptChunk(Base):
    """
    Chunked and embedded transcript segments for retrieval.
    """
    __tablename__ = "transcript_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    transcript_id = Column(UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=True)  # Default to 384 for MiniLM, adjust as needed
    metadata = Column(JSONB, nullable=False, default=dict)  # speaker, timestamp, context
    
    # Relationships
    transcript = relationship("Transcript", back_populates="chunks")
    
    # Constraints and Indexes
    __table_args__ = (
        Index("idx_chunks_transcript_id", "transcript_id"),
        Index("idx_chunks_embedding", "embedding", postgresql_using="ivfflat", postgresql_with={"lists": 100}),
    )
    
    def __repr__(self) -> str:
        return f"<TranscriptChunk(id={self.id}, transcript_id={self.transcript_id}, index={self.chunk_index})>"


class Artifact(Base):
    """
    Generated artifacts (Markdown, HTML, etc.) for history and caching.
    """
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    artifact_type = Column(String(50), nullable=False)  # 'markdown', 'html', 'json', 'mermaid'
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication
    metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    session = relationship("Session", back_populates="artifacts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "artifact_type IN ('markdown', 'html', 'json', 'mermaid')", 
            name="valid_artifact_type"
        ),
        Index("idx_artifacts_session_created", "session_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, type={self.artifact_type}, title={self.title})>"
