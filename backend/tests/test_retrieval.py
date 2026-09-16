"""
Tests for RAG retrieval system.
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from app.retrieval.embedder import LocalEmbedder, OpenAIEmbedder
from app.retrieval.retriever import Retriever, RetrievalResult


class TestLocalEmbedder:
    """Tests for LocalEmbedder."""
    
    @patch('app.retrieval.embedder.SentenceTransformer')
    def test_initialization(self, mock_st):
        """Test local embedder initialization."""
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        embedder = LocalEmbedder(model_name="test-model")
        
        assert embedder.model is not None
        assert embedder.get_dimension() == 384
    
    @patch('app.retrieval.embedder.SentenceTransformer')
    def test_embed_text(self, mock_st):
        """Test single text embedding."""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_st.return_value = mock_model
        
        embedder = LocalEmbedder()
        embedding = embedder.embed_text("test text")
        
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
    
    @patch('app.retrieval.embedder.SentenceTransformer')
    def test_embed_batch(self, mock_st):
        """Test batch embedding."""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])
        mock_st.return_value = mock_model
        
        embedder = LocalEmbedder()
        embeddings = embedder.embed_batch(["text1", "text2"])
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 3


class TestOpenAIEmbedder:
    """Tests for OpenAIEmbedder."""
    
    @patch('app.retrieval.embedder.OpenAI')
    def test_initialization(self, mock_openai):
        """Test OpenAI embedder initialization."""
        embedder = OpenAIEmbedder(api_key="test-key")
        
        assert embedder.client is not None
        assert embedder.get_dimension() == 1536
    
    @patch('app.retrieval.embedder.OpenAI')
    def test_embed_text(self, mock_openai):
        """Test single text embedding with OpenAI."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        embedder = OpenAIEmbedder(api_key="test-key")
        embedding = embedder.embed_text("test text")
        
        assert len(embedding) == 1536


class TestRetriever:
    """Tests for Retriever."""
    
    def test_format_sources(self):
        """Test source formatting."""
        # Mock database session
        db = Mock()
        
        # Create retriever
        retriever = Retriever(db=db, top_k=5)
        
        # Create mock results
        results = [
            RetrievalResult(
                chunk_id="1",
                transcript_id="t1",
                episode_number=42,
                guest_name="Test Guest",
                title="Test Episode",
                content="Test content",
                score=0.9,
                metadata={}
            ),
            RetrievalResult(
                chunk_id="2",
                transcript_id="t1",  # Same transcript
                episode_number=42,
                guest_name="Test Guest",
                title="Test Episode",
                content="More content",
                score=0.8,
                metadata={}
            )
        ]
        
        sources = retriever.format_sources(results)
        
        # Should only list each transcript once
        assert "Episode 42" in sources
        assert "Test Guest" in sources
        assert sources.count("Episode 42") == 1  # Not duplicated


class TestRetrievalIntegration:
    """Integration tests for retrieval system."""
    
    @pytest.mark.skipif(True, reason="Requires database and embeddings")
    def test_end_to_end_retrieval(self):
        """Test complete retrieval workflow."""
        # This would require:
        # 1. Database with sample transcripts
        # 2. Generated embeddings
        # 3. Actual retriever initialization
        
        # Placeholder for future integration test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
