"""
Complete ingestion pipeline for loading and processing transcripts.
"""

from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session

from app.ingestion.loader import TranscriptLoader, TranscriptData
from app.ingestion.chunker import TranscriptChunker
from app.db.repositories import TranscriptRepository
from app.logging_config import get_logger

logger = get_logger(__name__)


class IngestionPipeline:
    """
    Complete pipeline for ingesting transcripts into the database.
    
    Steps:
    1. Load transcripts from files
    2. Chunk text into segments
    3. Store in database (embeddings added later)
    """
    
    def __init__(
        self,
        data_path: str,
        db: Session,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize the ingestion pipeline.
        
        Args:
            data_path: Path to transcript files
            db: Database session
            chunk_size: Optional chunk size override
            chunk_overlap: Optional overlap size override
        """
        self.loader = TranscriptLoader(data_path)
        self.chunker = TranscriptChunker(chunk_size, chunk_overlap)
        self.repo = TranscriptRepository(db)
        self.db = db
        
        logger.info("ingestion_pipeline_initialized", data_path=data_path)
    
    def ingest_all(
        self,
        pattern: str = "*",
        skip_existing: bool = True
    ) -> dict:
        """
        Ingest all transcript files from the data directory.
        
        Args:
            pattern: Glob pattern for file matching
            skip_existing: Skip transcripts that already exist in DB
        
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("starting_ingestion", pattern=pattern)
        
        stats = {
            "loaded": 0,
            "skipped": 0,
            "ingested": 0,
            "chunks_created": 0,
            "errors": 0
        }
        
        # Load all transcript files
        transcripts = self.loader.load_all(pattern)
        stats["loaded"] = len(transcripts)
        
        for transcript_data in transcripts:
            try:
                # Check if already exists (by episode number or title)
                if skip_existing:
                    if transcript_data.episode_number:
                        existing = self.repo.get_by_episode_number(transcript_data.episode_number)
                        if existing:
                            logger.info(
                                "skipping_existing_transcript",
                                episode=transcript_data.episode_number
                            )
                            stats["skipped"] += 1
                            continue
                
                # Ingest single transcript
                chunk_count = self.ingest_transcript(transcript_data)
                stats["ingested"] += 1
                stats["chunks_created"] += chunk_count
                
            except Exception as e:
                logger.error(
                    "transcript_ingestion_error",
                    title=transcript_data.title,
                    error=str(e),
                    exc_info=True
                )
                stats["errors"] += 1
        
        logger.info("ingestion_complete", **stats)
        return stats
    
    def ingest_transcript(self, transcript_data: TranscriptData) -> int:
        """
        Ingest a single transcript into the database.
        
        Args:
            transcript_data: Transcript to ingest
        
        Returns:
            Number of chunks created
        """
        logger.info(
            "ingesting_transcript",
            title=transcript_data.title,
            episode=transcript_data.episode_number
        )
        
        # Create transcript record
        transcript = self.repo.create_transcript(
            title=transcript_data.title,
            full_text=transcript_data.full_text,
            episode_number=transcript_data.episode_number,
            guest_name=transcript_data.guest_name,
            publish_date=transcript_data.publish_date,
            duration_minutes=transcript_data.duration_minutes,
            summary=transcript_data.summary,
            topics=transcript_data.topics,
            url=transcript_data.url
        )
        
        # Chunk the text
        chunks = self.chunker.chunk_text(transcript_data.full_text)
        
        # Store chunks (embeddings will be added in separate step)
        for chunk in chunks:
            self.repo.create_chunk(
                transcript_id=transcript.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                embedding=None,  # Will be populated by embedding service
                metadata=chunk.metadata
            )
        
        logger.info(
            "transcript_ingested",
            transcript_id=str(transcript.id),
            chunks_created=len(chunks)
        )
        
        return len(chunks)
    
    def get_statistics(self) -> dict:
        """
        Get current database statistics.
        
        Returns:
            Dictionary with transcript and chunk counts
        """
        return {
            "total_transcripts": self.repo.count_transcripts(),
            "total_chunks": self.repo.count_chunks()
        }


def run_ingestion(data_path: str, db: Session) -> dict:
    """
    Convenience function to run the full ingestion pipeline.
    
    Args:
        data_path: Path to transcript files
        db: Database session
    
    Returns:
        Ingestion statistics
    """
    pipeline = IngestionPipeline(data_path, db)
    return pipeline.ingest_all()
