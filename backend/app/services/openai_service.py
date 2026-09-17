"""
OpenAI service for LLM chat and embeddings
"""
import logging
from typing import List, Optional
from openai import OpenAI, OpenAIError as OpenAIAPIError

from app.core import settings
from app.core.exceptions import OpenAIError

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        try:
            if not settings.openai_api_key:
                raise OpenAIError("OpenAI API key not configured")
            
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.llm_model = settings.llm_model
            self.embedding_model = settings.embedding_model
            logger.info(f"OpenAI service initialized with model: {self.llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}")
            raise OpenAIError("OpenAI initialization failed", {"error": str(e)})
    
    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
            
        Raises:
            OpenAIError: If API call fails
        """
        try:
            if not messages:
                raise OpenAIError("No messages provided")
            
            logger.info(f"Calling OpenAI chat with {len(messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI response received: {len(content)} characters")
            
            return content
            
        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise OpenAIError("OpenAI chat request failed", {"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI chat: {str(e)}")
            raise OpenAIError("Chat request failed", {"error": str(e)})
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            OpenAIError: If embedding generation fails
        """
        try:
            if not text or not text.strip():
                raise OpenAIError("Empty text provided for embedding")
            
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Embedding generated: {len(embedding)} dimensions")
            
            return embedding
            
        except OpenAIAPIError as e:
            logger.error(f"OpenAI embedding API error: {str(e)}")
            raise OpenAIError("Embedding generation failed", {"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {str(e)}")
            raise OpenAIError("Embedding generation failed", {"error": str(e)})
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            OpenAIError: If batch embedding fails
        """
        try:
            if not texts:
                raise OpenAIError("Empty text list provided")
            
            logger.info(f"Generating {len(texts)} embeddings in batch")
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
            
            # Sort by index to maintain order
            embeddings = sorted(response.data, key=lambda x: x.index)
            result = [item.embedding for item in embeddings]
            
            logger.info(f"Batch embeddings generated successfully")
            return result
            
        except OpenAIAPIError as e:
            logger.error(f"OpenAI batch embedding API error: {str(e)}")
            raise OpenAIError("Batch embedding failed", {"error": str(e)})
        except Exception as e:
            logger.error(f"Unexpected error in batch embedding: {str(e)}")
            raise OpenAIError("Batch embedding failed", {"error": str(e)})


# Global service instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get or create global OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
