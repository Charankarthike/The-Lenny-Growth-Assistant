#!/usr/bin/env python
"""
Script to ingest Lenny's Podcast transcripts into the database.

Usage:
    python scripts/ingest_transcripts.py
    python scripts/ingest_transcripts.py --data-path /path/to/transcripts
    python scripts/ingest_transcripts.py --pattern "episode_*.json"
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db.base import SessionLocal
from app.ingestion.pipeline import IngestionPipeline
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(
        description="Ingest Lenny's Podcast transcripts into the database"
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default=settings.transcript_data_path,
        help='Path to transcript files directory'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*',
        help='Glob pattern for file matching (e.g., "*.json")'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        default=True,
        help='Skip transcripts that already exist in database'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-ingestion of existing transcripts'
    )
    
    args = parser.parse_args()
    
    logger.info(
        "starting_ingestion_script",
        data_path=args.data_path,
        pattern=args.pattern,
        skip_existing=not args.force
    )
    
    # Validate data path
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error("data_path_not_found", path=str(data_path))
        print(f"Error: Data path not found: {data_path}")
        print(f"Please create the directory and add transcript files.")
        return 1
    
    # Check if directory has any files
    files = list(data_path.glob(args.pattern))
    if not files:
        logger.warning("no_files_found", path=str(data_path), pattern=args.pattern)
        print(f"Warning: No files matching pattern '{args.pattern}' found in {data_path}")
        print("Supported formats: .json, .md, .markdown, .html, .htm, .txt")
        return 1
    
    print(f"Found {len(files)} file(s) to process")
    print(f"Data path: {data_path}")
    print(f"Pattern: {args.pattern}")
    print(f"Skip existing: {not args.force}")
    print()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Run ingestion pipeline
        pipeline = IngestionPipeline(
            data_path=str(data_path),
            db=db
        )
        
        print("Starting ingestion...")
        stats = pipeline.ingest_all(
            pattern=args.pattern,
            skip_existing=not args.force
        )
        
        # Display results
        print()
        print("=" * 50)
        print("INGESTION COMPLETE")
        print("=" * 50)
        print(f"Files loaded:       {stats['loaded']}")
        print(f"Transcripts skipped: {stats['skipped']}")
        print(f"Transcripts ingested: {stats['ingested']}")
        print(f"Chunks created:     {stats['chunks_created']}")
        print(f"Errors:             {stats['errors']}")
        print()
        
        # Get current database stats
        db_stats = pipeline.get_statistics()
        print("Database Statistics:")
        print(f"Total transcripts:  {db_stats['total_transcripts']}")
        print(f"Total chunks:       {db_stats['total_chunks']}")
        
        if stats['errors'] > 0:
            print()
            print("⚠️  Some errors occurred. Check logs for details.")
            return 1
        
        print()
        print("✅ Ingestion successful!")
        print()
        print("Next steps:")
        print("  1. Generate embeddings: python scripts/generate_embeddings.py")
        print("  2. Test retrieval: python scripts/test_retrieval.py")
        
        return 0
        
    except Exception as e:
        logger.error("ingestion_failed", error=str(e), exc_info=True)
        print(f"\n❌ Ingestion failed: {e}")
        return 1
    
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
