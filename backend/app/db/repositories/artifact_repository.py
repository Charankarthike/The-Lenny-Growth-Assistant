"""
Repository for artifact operations.
"""

from typing import Optional, List
from uuid import UUID
import hashlib

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.db.models import Artifact
from app.logging_config import get_logger

logger = get_logger(__name__)


class ArtifactRepository:
    """Repository for artifact CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA-256 hash of content for deduplication.
        
        Args:
            content: Content to hash
        
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def create(
        self,
        session_id: UUID,
        artifact_type: str,
        content: str,
        title: Optional[str] = None,
        message_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> Artifact:
        """
        Create a new artifact.
        
        Args:
            session_id: UUID of the parent session
            artifact_type: Type of artifact ('markdown', 'html', 'json', 'mermaid')
            content: Artifact content
            title: Optional title
            message_id: Optional associated message ID
            metadata: Optional metadata
        
        Returns:
            Created artifact object
        """
        content_hash = self.compute_content_hash(content)
        
        artifact = Artifact(
            session_id=session_id,
            message_id=message_id,
            artifact_type=artifact_type,
            title=title,
            content=content,
            content_hash=content_hash,
            metadata=metadata or {}
        )
        
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        
        logger.info(
            "artifact_created",
            artifact_id=str(artifact.id),
            session_id=str(session_id),
            artifact_type=artifact_type,
            content_length=len(content)
        )
        
        return artifact
    
    def get_by_id(self, artifact_id: UUID) -> Optional[Artifact]:
        """
        Get an artifact by ID.
        
        Args:
            artifact_id: UUID of the artifact
        
        Returns:
            Artifact object or None if not found
        """
        query = select(Artifact).where(Artifact.id == artifact_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def list_by_session(
        self,
        session_id: UUID,
        artifact_type: Optional[str] = None
    ) -> List[Artifact]:
        """
        List artifacts for a session.
        
        Args:
            session_id: UUID of the session
            artifact_type: Optional filter by artifact type
        
        Returns:
            List of artifacts ordered by creation time (most recent first)
        """
        query = select(Artifact).where(Artifact.session_id == session_id)
        
        if artifact_type:
            query = query.where(Artifact.artifact_type == artifact_type)
        
        query = query.order_by(desc(Artifact.created_at))
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def find_by_content_hash(
        self,
        content_hash: str,
        session_id: Optional[UUID] = None
    ) -> Optional[Artifact]:
        """
        Find an artifact by content hash for deduplication.
        
        Args:
            content_hash: SHA-256 hash of content
            session_id: Optional session ID to scope search
        
        Returns:
            Artifact with matching hash or None
        """
        query = select(Artifact).where(Artifact.content_hash == content_hash)
        
        if session_id:
            query = query.where(Artifact.session_id == session_id)
        
        query = query.order_by(desc(Artifact.created_at)).limit(1)
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_latest_by_session(self, session_id: UUID) -> Optional[Artifact]:
        """
        Get the most recent artifact for a session.
        
        Args:
            session_id: UUID of the session
        
        Returns:
            Most recent artifact or None
        """
        query = (
            select(Artifact)
            .where(Artifact.session_id == session_id)
            .order_by(desc(Artifact.created_at))
            .limit(1)
        )
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
