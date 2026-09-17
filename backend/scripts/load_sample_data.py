"""
Load sample transcript data for testing
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core import get_db
from app.models.transcript import Transcript, TranscriptChunk
from app.services.openai_service import get_openai_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample transcript data
SAMPLE_TRANSCRIPTS = [
    {
        "episode_number": "001",
        "title": "Introduction to Product Growth",
        "guest": "Lenny Rachitsky",
        "date": "2024-01-01",
        "content": """
        Welcome to the Lenny Growth Assistant! In this episode, we discuss the fundamentals 
        of product growth. Product growth is about finding sustainable ways to grow your 
        product's user base and engagement. The key principles include: understanding your 
        users deeply, building features they actually need, measuring what matters, and 
        iterating quickly based on data. Successful product growth requires a combination 
        of qualitative user research and quantitative metrics analysis.
        """
    },
    {
        "episode_number": "002",
        "title": "Ship 30 for 30 Framework",
        "guest": "Dickie Bush",
        "date": "2024-01-08",
        "content": """
        Ship 30 for 30 is a powerful framework for building a writing habit and growing your 
        audience. The concept is simple: write and publish 30 short-form posts in 30 days. 
        Each post should be 250-300 words, focused on a single clear idea. The framework helps 
        you overcome perfectionism, build momentum, and discover what resonates with your 
        audience. Many successful creators used Ship 30 for 30 to launch their writing careers. 
        The key is consistency over perfection - just ship every single day.
        """
    },
    {
        "episode_number": "003",
        "title": "Product-Market Fit Indicators",
        "guest": "Rahul Vohra",
        "date": "2024-01-15",
        "content": """
        Product-market fit is the holy grail for startups, but how do you know when you have it? 
        Key indicators include: users are actively engaging with your product daily or weekly, 
        organic word-of-mouth growth is happening, retention curves are flattening (not decaying), 
        and users express strong disappointment if they couldn't use your product anymore. 
        The Sean Ellis test asks users how disappointed they'd be if the product disappeared - 
        if 40% or more say "very disappointed", you likely have PMF. Focus on depth before breadth.
        """
    },
]


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into chunks of approximately chunk_size characters"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


async def load_sample_data():
    """Load sample transcripts and generate embeddings"""
    try:
        logger.info("Loading sample transcript data...")
        
        openai_service = get_openai_service()
        
        with get_db() as db:
            # Clear existing data
            logger.info("Clearing existing data...")
            db.query(TranscriptChunk).delete()
            db.query(Transcript).delete()
            db.commit()
            
            total_chunks = 0
            
            for transcript_data in SAMPLE_TRANSCRIPTS:
                logger.info(f"Processing episode {transcript_data['episode_number']}: {transcript_data['title']}")
                
                # Create transcript
                transcript = Transcript(
                    episode_number=transcript_data["episode_number"],
                    title=transcript_data["title"],
                    guest=transcript_data["guest"],
                    date=transcript_data["date"],
                    content=transcript_data["content"].strip(),
                    metadata={}
                )
                db.add(transcript)
                db.flush()  # Get the transcript ID
                
                # Chunk the content
                chunks = chunk_text(transcript_data["content"].strip())
                logger.info(f"  Created {len(chunks)} chunks")
                
                # Generate embeddings for all chunks
                logger.info(f"  Generating embeddings...")
                embeddings = await openai_service.get_embeddings_batch(chunks)
                
                # Create chunk records with embeddings
                for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk = TranscriptChunk(
                        transcript_id=transcript.id,
                        episode_number=transcript.episode_number,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                        title=transcript.title,
                        guest=transcript.guest,
                        metadata={}
                    )
                    db.add(chunk)
                    total_chunks += 1
                
                logger.info(f"  ✅ Episode {transcript_data['episode_number']} loaded")
            
            db.commit()
            
            logger.info(f"✅ Successfully loaded {len(SAMPLE_TRANSCRIPTS)} transcripts with {total_chunks} chunks")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Failed to load sample data: {str(e)}", exc_info=True)
        return 1


def main():
    """Main entry point"""
    return asyncio.run(load_sample_data())


if __name__ == "__main__":
    sys.exit(main())
