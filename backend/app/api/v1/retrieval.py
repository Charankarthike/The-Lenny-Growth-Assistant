"""
Retrieval API endpoints for testing and debugging.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.retrieval.retriever import Retriever, RetrievalResult
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class SearchRequest(BaseModel):
    """Request model for search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")
    filter_by_guest: Optional[str] = Field(None, description="Filter by guest name")


class SearchResultResponse(BaseModel):
    """Response model for a single search result."""
    chunk_id: str
    transcript_id: str
    episode_number: Optional[int]
    guest_name: Optional[str]
    title: str
    content: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    """Response model for search."""
    results: List[SearchResultResponse]
    query: str
    num_results: int
    query_time_ms: Optional[float]


class StatsResponse(BaseModel):
    """Response model for retrieval statistics."""
    total_transcripts: int
    total_chunks: int
    chunks_with_embeddings: int
    embedding_coverage: float
    top_k: int
    min_score: float


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search for relevant transcript chunks.
    
    This endpoint is primarily for testing and debugging the retrieval system.
    Production chat should use the messages endpoint which includes retrieval.
    
    Args:
        request: Search parameters
        db: Database session
    
    Returns:
        Search results with source attribution
    """
    import time
    start_time = time.time()
    
    logger.info(
        "search_request",
        query=request.query,
        top_k=request.top_k,
        filter_by_guest=request.filter_by_guest
    )
    
    # Initialize retriever
    retriever = Retriever(
        db=db,
        top_k=request.top_k,
        min_score=request.min_score
    )
    
    # Perform search
    results = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        min_score=request.min_score,
        filter_by_guest=request.filter_by_guest
    )
    
    query_time = (time.time() - start_time) * 1000
    
    # Convert to response format
    result_responses = [
        SearchResultResponse(
            chunk_id=r.chunk_id,
            transcript_id=r.transcript_id,
            episode_number=r.episode_number,
            guest_name=r.guest_name,
            title=r.title,
            content=r.content,
            score=r.score,
            metadata=r.metadata
        )
        for r in results
    ]
    
    return SearchResponse(
        results=result_responses,
        query=request.query,
        num_results=len(results),
        query_time_ms=query_time
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """
    Get retrieval system statistics.
    
    Returns information about the number of transcripts, chunks,
    and embedding coverage.
    
    Args:
        db: Database session
    
    Returns:
        Statistics about the retrieval system
    """
    retriever = Retriever(db=db)
    stats = retriever.get_statistics()
    
    return StatsResponse(**stats)
