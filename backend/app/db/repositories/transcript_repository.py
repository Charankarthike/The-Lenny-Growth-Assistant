"""
Repository for transcript operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.db.models import Transcript, TranscriptChunk
from app.logging_config import get_logger

logger = get_logger(__name__)


class TranscriptRepository:
    """Repository for transcript and chunk operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_transcript(
        self,
        title: str,
        full_text: str,
        episode_number: Optional[int] = None,
        guest_name: Optional[str] = None,
        publish_date: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        summary: Optional[str] = None,
        topics: Optional[List[str]] = None,
        url: Optional[str] = None
    ) -> Transcript:
        """
        Create a new transcript.
        
        Args:
            title: Episode title
            full_text: Complete transcript text
            episode_number: Optional episode number
            guest_name: Optional guest name
            publish_date: Optional publish date
            duration_minutes: Optional duration
            summary: Optional AI-generated summary
            topics: Optional list of topic tags
            url: Optional source URL
        
        Returns:
            Created transcript object
        """
        transcript = Transcript(
            title=title,
            full_text=full_text,
            episode_number=episode_number,
            guest_name=guest_name,
            publish_date=publish_date,
            duration_minutes=duration_minutes,
            summary=summary,
            topics=topics,
            url=url
        )
        
        self.db.add(transcript)
        self.db.commit()
        self.db.refresh(transcript)
        
        logger.info(
            "transcript_created",
            transcript_id=str(transcript.id),
            episode_number=episode_number,
            guest_name=guest_name
        )
        
        return transcript
    
    def get_by_id(
        self,
        transcript_id: UUID,
        include_chunks: bool = False
    ) -> Optional[Transcript]:
        """
        Get a transcript by ID.
        
        Args:
            transcript_id: UUID of the transcript
            include_chunks: Whether to eagerly load chunks
        
        Returns:
            Transcript object or None if not found
        """
        query = select(Transcript).where(Transcript.id == transcript_id)
        
        if include_chunks:
            query = query.options(selectinload(Transcript.chunks))
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_by_episode_number(self, episode_number: int) -> Optional[Transcript]:
        """
        Get a transcript by episode number.
        
        Args:
            episode_number: Episode number
        
        Returns:
            Transcript object or None if not found
        """
        query = select(Transcript).where(Transcript.episode_number == episode_number)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        guest_name: Optional[str] = None
    ) -> tuple[List[Transcript], int]:
        """
        List transcripts with pagination.
        
        Args:
            limit: Maximum number of transcripts to return
            offset: Number of transcripts to skip
            guest_name: Optional filter by guest name
        
        Returns:
            Tuple of (list of transcripts, total count)
        """
        query = select(Transcript)
        
        if guest_name:
            query = query.where(Transcript.guest_name.ilike(f"%{guest_name}%"))
        
        # Get total count
        count_query = select(func.count(Transcript.id))
        if guest_name:
            count_query = count_query.where(Transcript.guest_name.ilike(f"%{guest_name}%"))
        
        total = self.db.execute(count_query).scalar()
        
        # Add ordering and pagination
        query = (
            query
            .order_by(Transcript.publish_date.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        
        result = self.db.execute(query)
        transcripts = result.scalars().all()
        
        return list(transcripts), total
    
    def create_chunk(
        self,
        transcript_id: UUID,
        chunk_index: int,
        content: str,
        token_count: int,
        embedding: Optional[List[float]] = None,
        metadata: Optional[dict] = None
    ) -> TranscriptChunk:
        """
        Create a transcript chunk with embedding.
        
        Args:
            transcript_id: UUID of the parent transcript
            chunk_index: Index of the chunk within the transcript
            content: Chunk text content
            token_count: Number of tokens in the chunk
            embedding: Optional embedding vector
            metadata: Optional metadata (speaker, timestamp, context)
        
        Returns:
            Created chunk object
        """
        chunk = TranscriptChunk(
            transcript_id=transcript_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        
        return chunk
    
    def get_chunks_by_transcript(
        self,
        transcript_id: UUID
    ) -> List[TranscriptChunk]:
        """
        Get all chunks for a transcript, ordered by index.
        
        Args:
            transcript_id: UUID of the transcript
        
        Returns:
            List of chunks in order
        """
        query = (
            select(TranscriptChunk)
            .where(TranscriptChunk.transcript_id == transcript_id)
            .order_by(TranscriptChunk.chunk_index)
        )
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def search_chunks_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.7
    ) -> List[tuple[TranscriptChunk, float]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Using pgvector's cosine distance
        # Note: cosine_distance returns distance (0 = identical, 2 = opposite)
        # We convert to similarity score (1 - distance/2)
        
        from pgvector.sqlalchemy import l2_distance
        
        query = (
            select(
                TranscriptChunk,
                (1 - l2_distance(TranscriptChunk.embedding, query_embedding) / 2).label("similarity")
            )
            .where(TranscriptChunk.embedding.isnot(None))
            .order_by(l2_distance(TranscriptChunk.embedding, query_embedding))
            .limit(top_k)
        )
        
        result = self.db.execute(query)
        results = []
        
        for row in result:
            chunk = row[0]
            similarity = float(row[1])
            
            if similarity >= min_score:
                results.append((chunk, similarity))
        
        return results
    
    def count_transcripts(self) -> int:
        """
        Get total number of transcripts.
        
        Returns:
            Total transcript count
        """
        query = select(func.count(Transcript.id))
        return self.db.execute(query).scalar()
    
    def count_chunks(self) -> int:
        """
        Get total number of chunks.
        
        Returns:
            Total chunk count
        """
        query = select(func.count(TranscriptChunk.id))
        return self.db.execute(query).scalar()
