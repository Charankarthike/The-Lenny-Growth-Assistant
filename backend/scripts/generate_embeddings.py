#!/usr/bin/env python
"""
Script to generate embeddings for all transcript chunks.

Usage:
    python scripts/generate_embeddings.py
    python scripts/generate_embeddings.py --batch-size 64
    python scripts/generate_embeddings.py --force  # Regenerate all
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db.base import SessionLocal
from app.db.models import TranscriptChunk
from app.retrieval.embedder import get_global_embedder
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Main entry point for embedding generation script."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for transcript chunks"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for embedding generation'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate embeddings for all chunks (even if they already exist)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of chunks to process (for testing)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EMBEDDING GENERATION")
    print("=" * 60)
    print()
    
    # Initialize embedder
    print("Initializing embedding model...")
    try:
        embedder = get_global_embedder()
        dimension = embedder.get_dimension()
        print(f"✓ Embedder loaded: {settings.embedding_provider}")
        print(f"  Model: {settings.local_embedding_model if settings.embedding_provider == 'local' else 'text-embedding-ada-002'}")
        print(f"  Dimension: {dimension}")
    except Exception as e:
        print(f"✗ Failed to load embedder: {e}")
        return 1
    
    print()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get chunks that need embeddings
        query = db.query(TranscriptChunk)
        
        if not args.force:
            # Only process chunks without embeddings
            query = query.filter(TranscriptChunk.embedding.is_(None))
        
        if args.limit:
            query = query.limit(args.limit)
        
        chunks = query.all()
        
        if not chunks:
            print("No chunks need embeddings. All done!")
            return 0
        
        print(f"Found {len(chunks)} chunks to process")
        print(f"Batch size: {args.batch_size}")
        print()
        
        # Process in batches
        total_processed = 0
        total_errors = 0
        
        for i in tqdm(range(0, len(chunks), args.batch_size), desc="Processing batches"):
            batch = chunks[i:i + args.batch_size]
            
            try:
                # Extract text from chunks
                texts = [chunk.content for chunk in batch]
                
                # Generate embeddings
                embeddings = embedder.embed_batch(texts, batch_size=args.batch_size)
                
                # Update database
                for chunk, embedding in zip(batch, embeddings):
                    chunk.embedding = embedding
                
                db.commit()
                total_processed += len(batch)
                
            except Exception as e:
                logger.error("batch_embedding_failed", 
                           batch_start=i,
                           error=str(e))
                db.rollback()
                total_errors += len(batch)
                print(f"\n✗ Error processing batch starting at {i}: {e}")
        
        print()
        print("=" * 60)
        print("EMBEDDING GENERATION COMPLETE")
        print("=" * 60)
        print(f"Successfully processed: {total_processed} chunks")
        print(f"Errors: {total_errors} chunks")
        print()
        
        # Get final statistics
        total_chunks = db.query(TranscriptChunk).count()
        chunks_with_embeddings = db.query(TranscriptChunk).filter(
            TranscriptChunk.embedding.isnot(None)
        ).count()
        
        coverage = (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0
        
        print("Database Statistics:")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Chunks with embeddings: {chunks_with_embeddings}")
        print(f"  Coverage: {coverage:.1f}%")
        
        if coverage < 100:
            print()
            print(f"⚠️  {total_chunks - chunks_with_embeddings} chunks still need embeddings")
            print("   Run this script again to process remaining chunks.")
        else:
            print()
            print("✓ All chunks have embeddings!")
        
        print()
        print("Next steps:")
        print("  1. Test retrieval: python scripts/test_retrieval.py")
        print("  2. Start the server: uvicorn app.main:app --reload")
        
        return 0 if total_errors == 0 else 1
        
    except Exception as e:
        logger.error("embedding_generation_failed", error=str(e), exc_info=True)
        print(f"\n❌ Embedding generation failed: {e}")
        return 1
    
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
