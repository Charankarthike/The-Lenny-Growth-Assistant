"""
Database initialization script.
Creates all tables and sets up pgvector extension.
"""

from sqlalchemy import text

from app.db.base import engine, Base
from app.db.models import Session, Message, Transcript, TranscriptChunk, Artifact
from app.logging_config import get_logger

logger = get_logger(__name__)


def init_database():
    """
    Initialize the database by:
    1. Creating pgvector extension
    2. Creating all tables
    """
    logger.info("initializing_database")
    
    # Create pgvector extension
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("pgvector_extension_created")
        except Exception as e:
            logger.error("failed_to_create_pgvector_extension", error=str(e))
            raise
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created")
    except Exception as e:
        logger.error("failed_to_create_tables", error=str(e))
        raise
    
    logger.info("database_initialization_complete")


def drop_all_tables():
    """
    Drop all tables. Use with caution!
    """
    logger.warning("dropping_all_tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("all_tables_dropped")


if __name__ == "__main__":
    init_database()
