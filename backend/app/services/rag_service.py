"""
RAG (Retrieval Augmented Generation) service
"""
import logging
from typing import List, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core import get_db, settings
from app.core.exceptions import RAGError, DatabaseError
from app.models.transcript import TranscriptChunk
from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG retrieval and context augmentation"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.openai_service = get_openai_service()
        self.top_k = settings.top_k_results
        logger.info(f"RAG service initialized with top_k={self.top_k}")
    
    async def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = None,
    ) -> List[Tuple[TranscriptChunk, float]]:
        """
        Retrieve most relevant transcript chunks for a query
        
        Args:
            query: User's question/query
            top_k: Number of results to return (default from settings)
            
        Returns:
            List of (chunk, similarity_score) tuples
            
        Raises:
            RAGError: If retrieval fails
        """
        if top_k is None:
            top_k = self.top_k
        
        try:
            if not query or not query.strip():
                raise RAGError("Empty query provided")
            
            logger.info(f"Retrieving relevant chunks for query: {query[:100]}...")
            
            # Generate embedding for query
            query_embedding = await self.openai_service.get_embedding(query)
            
            # Convert embedding to PostgreSQL array format
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Vector similarity search using pgvector
            try:
                with get_db() as db:
                    sql = text("""
                        SELECT 
                            id,
                            transcript_id,
                            episode_number,
                            chunk_index,
                            content,
                            title,
                            guest,
                            metadata,
                            1 - (embedding <=> :query_embedding::vector) as similarity
                        FROM transcript_chunks
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> :query_embedding::vector
                        LIMIT :top_k
                    """)
                    
                    result = db.execute(
                        sql,
                        {"query_embedding": embedding_str, "top_k": top_k}
                    )
                    
                    rows = result.fetchall()
                    
                    if not rows:
                        logger.warning("No chunks found in database")
                        return []
                    
                    # Convert to chunks with scores
                    chunks_with_scores = []
                    for row in rows:
                        chunk = TranscriptChunk(
                            id=row[0],
                            transcript_id=row[1],
                            episode_number=row[2],
                            chunk_index=row[3],
                            content=row[4],
                            title=row[5],
                            guest=row[6],
                            metadata=row[7] or {},
                        )
                        similarity = float(row[8])
                        chunks_with_scores.append((chunk, similarity))
                    
                    logger.info(f"Retrieved {len(chunks_with_scores)} relevant chunks")
                    return chunks_with_scores
                    
            except SQLAlchemyError as e:
                logger.error(f"Database error during retrieval: {str(e)}")
                raise DatabaseError("Failed to retrieve chunks from database", {"error": str(e)})
                
        except (RAGError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in RAG retrieval: {str(e)}", exc_info=True)
            raise RAGError("RAG retrieval failed", {"error": str(e)})
    
    def build_rag_context(
        self,
        chunks_with_scores: List[Tuple[TranscriptChunk, float]]
    ) -> str:
        """
        Build context string from retrieved chunks
        
        Args:
            chunks_with_scores: List of (chunk, score) tuples
            
        Returns:
            Formatted context string
        """
        if not chunks_with_scores:
            return ""
        
        context_parts = [
            "Here is relevant context from Lenny's podcast transcripts:\n"
        ]
        
        for i, (chunk, score) in enumerate(chunks_with_scores, 1):
            episode_info = f"Episode {chunk.episode_number}"
            if chunk.title:
                episode_info += f": {chunk.title}"
            if chunk.guest:
                episode_info += f" (Guest: {chunk.guest})"
            
            context_parts.append(
                f"\n[Source {i}] {episode_info}\n"
                f"{chunk.content}\n"
            )
        
        return "\n".join(context_parts)
    
    async def get_rag_response(
        self,
        query: str,
        conversation_history: List[dict] = None,
    ) -> Tuple[str, List[dict]]:
        """
        Get RAG-augmented response for a query
        
        Args:
            query: User's question
            conversation_history: Previous messages in conversation
            
        Returns:
            Tuple of (response_text, sources)
        """
        try:
            # Retrieve relevant chunks
            chunks_with_scores = await self.retrieve_relevant_chunks(query)
            
            if not chunks_with_scores:
                logger.warning("No relevant chunks found, using basic chat")
                response = await self.openai_service.chat(
                    messages=conversation_history or [],
                    temperature=0.7,
                    max_tokens=2000,
                )
                return response, []
            
            # Build context
            context = self.build_rag_context(chunks_with_scores)
            
            # Create RAG prompt
            system_message = {
                "role": "system",
                "content": (
                    "You are Lenny's Growth Assistant, an AI trained on Lenny Rachitsky's "
                    "podcast content. Use the provided context from podcast transcripts to "
                    "answer questions accurately. If the context doesn't contain relevant "
                    "information, say so and provide a general answer based on your knowledge. "
                    "Always cite which episode/source you're referencing when using the context."
                )
            }
            
            # Build messages with context
            messages = [system_message]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[:-1])  # Exclude last user message
            
            # Add context and current query
            messages.append({
                "role": "user",
                "content": f"{context}\n\nUser Question: {query}"
            })
            
            # Get response
            response = await self.openai_service.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )
            
            # Build sources list
            sources = []
            for chunk, score in chunks_with_scores:
                source = {
                    "title": chunk.title or f"Episode {chunk.episode_number}",
                    "content": chunk.content[:200] + "...",  # First 200 chars
                    "episode": chunk.episode_number,
                    "relevance_score": round(score, 3),
                }
                if chunk.guest:
                    source["guest"] = chunk.guest
                sources.append(source)
            
            return response, sources
            
        except Exception as e:
            logger.error(f"RAG response error: {str(e)}", exc_info=True)
            raise


# Global service instance
_rag_service = None


def get_rag_service() -> RAGService:
    """Get or create global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
