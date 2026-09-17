"""
Database models for transcripts and chunks
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Transcript(Base):
    """Podcast transcript model"""
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    episode_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    guest = Column(String)
    date = Column(String)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TranscriptChunk(Base):
    """Chunked transcript with embeddings for RAG"""
    __tablename__ = "transcript_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, index=True, nullable=False)
    episode_number = Column(String, index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    
    # Vector embedding (1536 dimensions for text-embedding-3-small)
    embedding = Column(Vector(1536))
    
    # Metadata
    title = Column(String)
    guest = Column(String)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TranscriptChunk(id={self.id}, episode={self.episode_number}, chunk={self.chunk_index})>"
