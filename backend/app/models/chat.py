"""
Chat request and response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class Message(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request from frontend"""
    messages: List[Message] = Field(..., description="Conversation history")
    stream: bool = Field(default=False, description="Enable streaming response")
    use_rag: bool = Field(default=True, description="Use RAG retrieval")


class Source(BaseModel):
    """Source citation for RAG responses"""
    title: str
    content: str
    episode: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Chat response to frontend"""
    response: str = Field(..., description="Assistant's response")
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    model_used: str = Field(..., description="LLM model used")
