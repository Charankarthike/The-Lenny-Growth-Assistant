"""
Repository for session operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, desc
from sqlalchemy.orm import Session, selectinload

from app.db.models import Session as SessionModel
from app.logging_config import get_logger

logger = get_logger(__name__)


class SessionRepository:
    """Repository for session CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        title: Optional[str],
        model_provider: str,
        model_name: str,
        metadata: Optional[dict] = None
    ) -> SessionModel:
        """
        Create a new session.
        
        Args:
            title: Optional session title
            model_provider: LLM provider name
            model_name: Specific model name
            metadata: Optional metadata dictionary
        
        Returns:
            Created session object
        """
        session = SessionModel(
            title=title,
            model_provider=model_provider,
            model_name=model_name,
            metadata=metadata or {}
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(
            "session_created",
            session_id=str(session.id),
            model_provider=model_provider,
            model_name=model_name
        )
        
        return session
    
    def get_by_id(
        self,
        session_id: UUID,
        include_messages: bool = False
    ) -> Optional[SessionModel]:
        """
        Get a session by ID.
        
        Args:
            session_id: UUID of the session
            include_messages: Whether to eagerly load messages
        
        Returns:
            Session object or None if not found
        """
        query = select(SessionModel).where(SessionModel.id == session_id)
        
        if include_messages:
            query = query.options(selectinload(SessionModel.messages))
        
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def list(
        self,
        limit: int = 20,
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> tuple[List[SessionModel], int]:
        """
        List sessions with pagination.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            is_active: Optional filter for active status
        
        Returns:
            Tuple of (list of sessions, total count)
        """
        # Build base query
        query = select(SessionModel)
        
        if is_active is not None:
            query = query.where(SessionModel.is_active == is_active)
        
        # Get total count
        count_query = select(SessionModel.id)
        if is_active is not None:
            count_query = count_query.where(SessionModel.is_active == is_active)
        
        total = len(self.db.execute(count_query).all())
        
        # Add ordering and pagination
        query = (
            query
            .order_by(desc(SessionModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = self.db.execute(query)
        sessions = result.scalars().all()
        
        return list(sessions), total
    
    def update(
        self,
        session_id: UUID,
        title: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[SessionModel]:
        """
        Update session attributes.
        
        Args:
            session_id: UUID of the session
            title: New title (if provided)
            metadata: New metadata (if provided)
        
        Returns:
            Updated session or None if not found
        """
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        if title is not None:
            session.title = title
        
        if metadata is not None:
            session.metadata = metadata
        
        session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info("session_updated", session_id=str(session_id))
        
        return session
    
    def soft_delete(self, session_id: UUID) -> bool:
        """
        Soft-delete a session by setting is_active = False.
        
        Args:
            session_id: UUID of the session
        
        Returns:
            True if deleted, False if not found
        """
        stmt = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        
        result = self.db.execute(stmt)
        self.db.commit()
        
        if result.rowcount > 0:
            logger.info("session_deleted", session_id=str(session_id))
            return True
        
        return False
    
    def get_message_count(self, session_id: UUID) -> int:
        """
        Get the number of messages in a session.
        
        Args:
            session_id: UUID of the session
        
        Returns:
            Number of messages
        """
        from app.db.models import Message
        
        query = select(Message.id).where(Message.session_id == session_id)
        result = self.db.execute(query)
        return len(result.all())
