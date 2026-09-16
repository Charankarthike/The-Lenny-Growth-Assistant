#!/usr/bin/env python
"""
Script to test the retrieval system with sample queries.

Usage:
    python scripts/test_retrieval.py
    python scripts/test_retrieval.py "What is product-market fit?"
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db.base import SessionLocal
from app.retrieval.retriever import Retriever
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


SAMPLE_QUERIES = [
    "What is product-market fit?",
    "How do you measure retention?",
    "What is a growth loop?",
    "What are good pricing strategies?",
    "How should I price my SaaS product?",
]


def test_query(retriever: Retriever, query: str, top_k: int = 3):
    """Test a single query and display results."""
    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    try:
        results = retriever.retrieve(query, top_k=top_k)
        
        if not results:
            print("\n⚠️  No results found.")
            return
        
        print(f"\nFound {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Episode {result.episode_number or '?'}: {result.title}")
            if result.guest_name:
                print(f"   Guest: {result.guest_name}")
            print(f"   Score: {result.score:.3f}")
            print(f"   Excerpt: {result.content[:200]}...")
            print()
        
        # Show sources
        print("\n📚 Sources:")
        print(retriever.format_sources(results))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error("retrieval_test_failed", query=query, error=str(e))


def main():
    """Main entry point for retrieval testing."""
    parser = argparse.ArgumentParser(
        description="Test the retrieval system"
    )
    parser.add_argument(
        'query',
        nargs='?',
        help='Query to test (if not provided, runs sample queries)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='Number of results to return'
    )
    parser.add_argument(
        '--all-samples',
        action='store_true',
        help='Run all sample queries'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("RETRIEVAL SYSTEM TEST")
    print("=" * 80)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize retriever
        print("\nInitializing retriever...")
        retriever = Retriever(db, top_k=args.top_k)
        
        # Get statistics
        stats = retriever.get_statistics()
        print(f"\n📊 System Statistics:")
        print(f"  Total transcripts: {stats['total_transcripts']}")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Chunks with embeddings: {stats['chunks_with_embeddings']}")
        print(f"  Coverage: {stats['embedding_coverage']:.1%}")
        print(f"  Retrieval settings: top_k={stats['top_k']}, min_score={stats['min_score']}")
        
        if stats['chunks_with_embeddings'] == 0:
            print("\n⚠️  No embeddings found in database!")
            print("   Run: python scripts/generate_embeddings.py")
            return 1
        
        # Run queries
        if args.query:
            # Test single query
            test_query(retriever, args.query, args.top_k)
        
        elif args.all_samples:
            # Test all sample queries
            for query in SAMPLE_QUERIES:
                test_query(retriever, query, args.top_k)
        
        else:
            # Interactive mode
            print("\n" + "=" * 80)
            print("INTERACTIVE MODE")
            print("=" * 80)
            print("\nType your queries (or 'quit' to exit):")
            print()
            
            while True:
                try:
                    query = input("\n🔍 Query: ").strip()
                    
                    if not query:
                        continue
                    
                    if query.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    test_query(retriever, query, args.top_k)
                
                except KeyboardInterrupt:
                    print("\n\nExiting...")
                    break
                except EOFError:
                    break
        
        return 0
        
    except Exception as e:
        logger.error("retrieval_test_failed", error=str(e), exc_info=True)
        print(f"\n❌ Test failed: {e}")
        return 1
    
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
