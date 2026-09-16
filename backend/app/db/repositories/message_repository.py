"""
Repository for message operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.db.models import Message
from app.logging_config import get_logger

logger = get_logger(__name__)


class MessageRepository:
    """Repository for message CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        session_id: UUID,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        Create a new message.
        
        Args:
            session_id: UUID of the parent session
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            token_count: Optional token count
            metadata: Optional metadata (sources, artifacts, etc.)
        
        Returns:
            Created message object
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(
            "message_created",
            message_id=str(message.id),
            session_id=str(session_id),
            role=role,
            content_length=len(content)
        )
        
        return message
    
    def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.
        
        Args:
            message_id: UUID of the message
        
        Returns:
            Message object or None if not found
        """
        query = select(Message).where(Message.id == message_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def list_by_session(
        self,
        session_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Message], int]:
        """
        List messages for a session with pagination.
        
        Args:
            session_id: UUID of the session
            limit: Maximum number of messages to return
            offset: Number of messages to skip
        
        Returns:
            Tuple of (list of messages, total count)
        """
        # Get total count
        count_query = select(Message.id).where(Message.session_id == session_id)
        total = len(self.db.execute(count_query).all())
        
        # Get messages ordered by creation time (chronological)
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
            .offset(offset)
        )
        
        result = self.db.execute(query)
        messages = result.scalars().all()
        
        return list(messages), total
    
    def get_recent_messages(
        self,
        session_id: UUID,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the most recent messages for context.
        
        Args:
            session_id: UUID of the session
            limit: Maximum number of messages to return
        
        Returns:
            List of recent messages in chronological order
        """
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        
        result = self.db.execute(query)
        messages = result.scalars().all()
        
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))
    
    def update_metadata(
        self,
        message_id: UUID,
        metadata: dict
    ) -> Optional[Message]:
        """
        Update message metadata.
        
        Args:
            message_id: UUID of the message
            metadata: New metadata dictionary
        
        Returns:
            Updated message or None if not found
        """
        message = self.get_by_id(message_id)
        if not message:
            return None
        
        message.metadata = metadata
        self.db.commit()
        self.db.refresh(message)
        
        logger.info("message_metadata_updated", message_id=str(message_id))
        
        return message
