"""
Check what data exists in the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core import get_db
from app.models.transcript import Transcript, TranscriptChunk
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Check database contents"""
    try:
        logger.info("Checking database contents...")
        
        with get_db() as db:
            # Count transcripts
            transcript_count = db.query(Transcript).count()
            logger.info(f"📄 Transcripts: {transcript_count}")
            
            # List transcripts
            if transcript_count > 0:
                transcripts = db.query(Transcript).all()
                for t in transcripts:
                    logger.info(f"  - Episode {t.episode_number}: {t.title}")
            
            # Count chunks
            chunk_count = db.query(TranscriptChunk).count()
            logger.info(f"📦 Chunks: {chunk_count}")
            
            # Count chunks with embeddings
            chunks_with_embeddings = db.query(TranscriptChunk).filter(
                TranscriptChunk.embedding.isnot(None)
            ).count()
            logger.info(f"🔢 Chunks with embeddings: {chunks_with_embeddings}")
            
            if chunk_count == 0:
                logger.warning("⚠️  No data found. Run 'python scripts/load_sample_data.py' to load sample data.")
            else:
                logger.info("✅ Database has data!")
            
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to check data: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
