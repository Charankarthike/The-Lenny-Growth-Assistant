"""
Main RAG retrieval engine for semantic search over transcripts.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.retrieval.embedder import get_global_embedder
from app.db.repositories import TranscriptRepository
from app.db.models import TranscriptChunk, Transcript
from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Result from retrieval system."""
    chunk_id: str
    transcript_id: str
    episode_number: Optional[int]
    guest_name: Optional[str]
    title: str
    content: str
    score: float
    metadata: dict


class Retriever:
    """
    Main retrieval engine for RAG.
    
    Workflow:
    1. Embed query text
    2. Search vector database for similar chunks
    3. Optionally rerank results
    4. Return grounded context with source attribution
    """
    
    def __init__(
        self,
        db: Session,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ):
        """
        Initialize the retriever.
        
        Args:
            db: Database session
            top_k: Number of results to return (default from settings)
            min_score: Minimum similarity score (default from settings)
        """
        self.db = db
        self.repo = TranscriptRepository(db)
        self.embedder = get_global_embedder()
        self.top_k = top_k or settings.retrieval_top_k
        self.min_score = min_score or settings.retrieval_min_score
        
        logger.info(
            "retriever_initialized",
            top_k=self.top_k,
            min_score=self.min_score
        )
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        filter_by_guest: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant transcript chunks for a query.
        
        Args:
            query: Search query
            top_k: Override number of results
            min_score: Override minimum score
            filter_by_guest: Optional guest name filter
        
        Returns:
            List of retrieval results with source attribution
        """
        k = top_k or self.top_k
        min_score = min_score or self.min_score
        
        logger.info(
            "starting_retrieval",
            query_length=len(query),
            top_k=k,
            min_score=min_score
        )
        
        # Step 1: Generate query embedding
        try:
            query_embedding = self.embedder.embed_text(query)
        except Exception as e:
            logger.error("query_embedding_failed", error=str(e))
            raise
        
        # Step 2: Search vector database
        try:
            chunk_results = self.repo.search_chunks_by_embedding(
                query_embedding=query_embedding,
                top_k=k * 2,  # Get more for filtering
                min_score=0.0  # We'll filter after
            )
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            raise
        
        # Step 3: Filter by guest if specified
        if filter_by_guest:
            chunk_results = [
                (chunk, score) for chunk, score in chunk_results
                if chunk.transcript.guest_name and 
                filter_by_guest.lower() in chunk.transcript.guest_name.lower()
            ]
        
        # Step 4: Filter by minimum score
        chunk_results = [
            (chunk, score) for chunk, score in chunk_results
            if score >= min_score
        ]
        
        # Step 5: Limit to top_k
        chunk_results = chunk_results[:k]
        
        # Step 6: Convert to RetrievalResult objects with full metadata
        results = []
        for chunk, score in chunk_results:
            # Get transcript metadata
            transcript = chunk.transcript
            
            result = RetrievalResult(
                chunk_id=str(chunk.id),
                transcript_id=str(transcript.id),
                episode_number=transcript.episode_number,
                guest_name=transcript.guest_name,
                title=transcript.title,
                content=chunk.content,
                score=score,
                metadata={
                    **chunk.metadata,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "publish_date": transcript.publish_date.isoformat() if transcript.publish_date else None,
                    "url": transcript.url
                }
            )
            results.append(result)
        
        logger.info(
            "retrieval_complete",
            num_results=len(results),
            avg_score=sum(r.score for r in results) / len(results) if results else 0
        )
        
        return results
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        context_window: int = 1
    ) -> List[Tuple[RetrievalResult, str]]:
        """
        Retrieve chunks with surrounding context.
        
        Args:
            query: Search query
            top_k: Number of results
            context_window: Number of chunks before/after to include
        
        Returns:
            List of (result, context_text) tuples
        """
        results = self.retrieve(query, top_k)
        
        results_with_context = []
        for result in results:
            # Get surrounding chunks
            chunk = self.db.query(TranscriptChunk).filter(
                TranscriptChunk.id == result.chunk_id
            ).first()
            
            if chunk:
                # Get adjacent chunks
                all_chunks = self.repo.get_chunks_by_transcript(chunk.transcript_id)
                
                start_idx = max(0, chunk.chunk_index - context_window)
                end_idx = min(len(all_chunks), chunk.chunk_index + context_window + 1)
                
                context_chunks = all_chunks[start_idx:end_idx]
                context_text = " [...] ".join(c.content for c in context_chunks)
                
                results_with_context.append((result, context_text))
            else:
                results_with_context.append((result, result.content))
        
        return results_with_context
    
    def format_sources(self, results: List[RetrievalResult]) -> str:
        """
        Format retrieval results as source citations.
        
        Args:
            results: List of retrieval results
        
        Returns:
            Formatted source citations
        """
        if not results:
            return "No sources found."
        
        sources = []
        seen_transcripts = set()
        
        for result in results:
            transcript_key = result.transcript_id
            if transcript_key not in seen_transcripts:
                seen_transcripts.add(transcript_key)
                
                source = f"Episode {result.episode_number or 'Unknown'}"
                if result.guest_name:
                    source += f" with {result.guest_name}"
                source += f": {result.title}"
                sources.append(source)
        
        return "\n".join(f"- {s}" for s in sources)
    
    def get_statistics(self) -> dict:
        """
        Get retrieval system statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_transcripts = self.repo.count_transcripts()
        total_chunks = self.repo.count_chunks()
        
        # Count chunks with embeddings
        chunks_with_embeddings = self.db.query(TranscriptChunk).filter(
            TranscriptChunk.embedding.isnot(None)
        ).count()
        
        return {
            "total_transcripts": total_transcripts,
            "total_chunks": total_chunks,
            "chunks_with_embeddings": chunks_with_embeddings,
            "embedding_coverage": chunks_with_embeddings / total_chunks if total_chunks > 0 else 0,
            "top_k": self.top_k,
            "min_score": self.min_score
        }
