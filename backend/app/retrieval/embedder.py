"""
Embedding generation for text using local or API-based models.
"""

from typing import List, Optional
import numpy as np

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class Embedder:
    """
    Abstract base class for embedding models.
    """
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        raise NotImplementedError
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        raise NotImplementedError


class LocalEmbedder(Embedder):
    """
    Local embedding model using sentence-transformers.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the local embedder.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name or settings.local_embedding_model
        self.model = None
        self._load_model()
        
        logger.info("local_embedder_initialized", model=self.model_name)
    
    def _load_model(self):
        """Load the sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("loading_embedding_model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            logger.info("embedding_model_loaded", 
                       model=self.model_name,
                       dimension=self.get_dimension())
        except Exception as e:
            logger.error("failed_to_load_embedding_model", 
                        model=self.model_name,
                        error=str(e))
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
        
        Returns:
            List of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        
        logger.info("embedding_batch", num_texts=len(texts))
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if not self.model:
            return settings.embedding_dimension
        return self.model.get_sentence_embedding_dimension()


class OpenAIEmbedder(Embedder):
    """
    OpenAI embedding model using text-embedding-ada-002.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI embedder.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("openai_embedder_initialized")
        except Exception as e:
            logger.error("failed_to_initialize_openai_embedder", error=str(e))
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("openai_embedding_error", error=str(e))
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        logger.info("embedding_batch_openai", num_texts=len(texts))
        
        try:
            # OpenAI API supports batch embeddings
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            # Sort by index to maintain order
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in embeddings]
        except Exception as e:
            logger.error("openai_batch_embedding_error", error=str(e))
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension (OpenAI ada-002 is 1536)."""
        return 1536


def get_embedder() -> Embedder:
    """
    Factory function to get the configured embedder.
    
    Returns:
        Embedder instance based on configuration
    """
    if settings.embedding_provider == "openai":
        return OpenAIEmbedder()
    else:  # local
        return LocalEmbedder()


# Global embedder instance (lazy loaded)
_embedder: Optional[Embedder] = None


def get_global_embedder() -> Embedder:
    """
    Get or create the global embedder instance.
    
    Returns:
        Global embedder instance
    """
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder
