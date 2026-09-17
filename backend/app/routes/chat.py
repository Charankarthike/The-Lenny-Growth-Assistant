"""
Chat endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.models.chat import ChatRequest, ChatResponse, Source
from app.services.openai_service import get_openai_service
from app.services.rag_service import get_rag_service
from app.core import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG retrieval
    
    If use_rag=True and database is available, uses RAG to augment responses
    with relevant content from Lenny's podcasts.
    """
    try:
        logger.info(f"Chat request received with {len(request.messages)} messages, use_rag={request.use_rag}")
        
        # Get the user's latest message
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages provided"
            )
        
        user_message = request.messages[-1].content
        
        # Convert messages to dict format for conversation history
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Try RAG if requested
        if request.use_rag:
            try:
                rag_service = get_rag_service()
                response_text, sources = await rag_service.get_rag_response(
                    query=user_message,
                    conversation_history=conversation_history,
                )
                
                # Convert sources to Source models
                source_models = [
                    Source(
                        title=src["title"],
                        content=src["content"],
                        episode=src.get("episode"),
                        relevance_score=src.get("relevance_score"),
                    )
                    for src in sources
                ]
                
                return ChatResponse(
                    response=response_text,
                    sources=source_models,
                    model_used=settings.llm_model,
                )
                
            except Exception as e:
                logger.warning(f"RAG failed, falling back to basic chat: {str(e)}")
                # Fall through to basic chat
        
        # Basic chat without RAG
        openai_service = get_openai_service()
        
        # Add system message if not present
        if not conversation_history or conversation_history[0].get("role") != "system":
            system_message = {
                "role": "system",
                "content": (
                    "You are Lenny's Growth Assistant, an AI trained on Lenny Rachitsky's "
                    "podcast content. You help answer questions about product growth, "
                    "product management, startups, and career development. "
                    "Be helpful, insightful, and conversational."
                )
            }
            conversation_history.insert(0, system_message)
        
        response_text = await openai_service.chat(
            messages=conversation_history,
            temperature=0.7,
            max_tokens=2000,
        )
        
        return ChatResponse(
            response=response_text,
            sources=[],
            model_used=settings.llm_model,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )
