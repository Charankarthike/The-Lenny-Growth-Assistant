"""
Initialize database - create tables and enable pgvector
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database"""
    try:
        logger.info("Starting database initialization...")
        init_db()
        logger.info("✅ Database initialized successfully!")
        return 0
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
