"""
Tests for transcript ingestion system.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.ingestion.loader import TranscriptLoader, TranscriptData
from app.ingestion.chunker import TranscriptChunker


class TestTranscriptLoader:
    """Tests for TranscriptLoader."""
    
    def test_load_json(self, tmp_path):
        """Test loading a JSON transcript."""
        # Create test file
        test_file = tmp_path / "test.json"
        test_data = {
            "title": "Test Episode",
            "episode_number": 42,
            "guest_name": "Test Guest",
            "transcript": "This is a test transcript."
        }
        test_file.write_text(json.dumps(test_data))
        
        # Load file
        loader = TranscriptLoader(str(tmp_path))
        transcript = loader.load_json(test_file)
        
        assert transcript.title == "Test Episode"
        assert transcript.episode_number == 42
        assert transcript.guest_name == "Test Guest"
        assert transcript.full_text == "This is a test transcript."
    
    def test_load_markdown(self, tmp_path):
        """Test loading a Markdown transcript."""
        test_file = tmp_path / "test.md"
        content = """---
title: Test Episode
episode: 42
guest: Test Guest
---

# Test Episode

This is a test transcript.
"""
        test_file.write_text(content)
        
        loader = TranscriptLoader(str(tmp_path))
        transcript = loader.load_markdown(test_file)
        
        assert transcript.title == "Test Episode"
        assert transcript.episode_number == 42
        assert transcript.guest_name == "Test Guest"
        assert "test transcript" in transcript.full_text.lower()
    
    def test_load_text(self, tmp_path):
        """Test loading a plain text transcript."""
        test_file = tmp_path / "test.txt"
        content = "Test Episode\n\nThis is a test transcript."
        test_file.write_text(content)
        
        loader = TranscriptLoader(str(tmp_path))
        transcript = loader.load_text(test_file)
        
        assert transcript.title == "Test Episode"
        assert "test transcript" in transcript.full_text.lower()
    
    def test_load_all(self, tmp_path):
        """Test loading all files from directory."""
        # Create multiple test files
        (tmp_path / "test1.json").write_text(json.dumps({
            "title": "Episode 1",
            "transcript": "Content 1"
        }))
        (tmp_path / "test2.json").write_text(json.dumps({
            "title": "Episode 2",
            "transcript": "Content 2"
        }))
        
        loader = TranscriptLoader(str(tmp_path))
        transcripts = loader.load_all("*.json")
        
        assert len(transcripts) == 2
        titles = [t.title for t in transcripts]
        assert "Episode 1" in titles
        assert "Episode 2" in titles


class TestTranscriptChunker:
    """Tests for TranscriptChunker."""
    
    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = TranscriptChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a short text that should fit in one chunk."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0
        assert chunks[0].content == text
    
    def test_chunk_long_text(self):
        """Test chunking text longer than chunk size."""
        chunker = TranscriptChunker(chunk_size=50, chunk_overlap=10)
        
        # Create text with multiple sentences
        sentences = [
            "This is the first sentence.",
            "This is the second sentence.",
            "This is the third sentence.",
            "This is the fourth sentence.",
            "This is the fifth sentence."
        ]
        text = " ".join(sentences)
        
        chunks = chunker.chunk_text(text)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Check chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
        
        # Check overlap exists between consecutive chunks
        if len(chunks) > 1:
            # Last words of first chunk should appear in second chunk
            first_chunk_words = chunks[0].content.split()[-3:]
            assert any(word in chunks[1].content for word in first_chunk_words)
    
    def test_token_counting(self):
        """Test token counting."""
        chunker = TranscriptChunker()
        text = "This is a test sentence with some words."
        
        token_count = chunker.count_tokens(text)
        
        # Should be approximately 8-10 tokens
        assert 5 < token_count < 15
    
    def test_metadata_extraction(self):
        """Test metadata extraction from chunk text."""
        chunker = TranscriptChunker()
        text = "Speaker: This is what the speaker said. [00:12:34] More content."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        metadata = chunks[0].metadata
        assert 'speaker' in metadata or 'timestamp' in metadata
    
    def test_chunk_with_context(self):
        """Test getting chunk with surrounding context."""
        chunker = TranscriptChunker(chunk_size=50, chunk_overlap=10)
        
        # Create multiple chunks
        text = " ".join([f"Sentence {i}." for i in range(20)])
        chunks = chunker.chunk_text(text)
        
        if len(chunks) >= 3:
            # Get middle chunk with context
            context = chunker.get_chunk_with_context(chunks, 1, context_size=1)
            
            # Should include content from chunks 0, 1, and 2
            assert len(context) > len(chunks[1].content)
            assert "[...]" in context  # Context separator


class TestIngestionIntegration:
    """Integration tests for the full ingestion pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test the complete ingestion flow."""
        # Create test transcript file
        test_file = tmp_path / "test.json"
        test_data = {
            "title": "Integration Test Episode",
            "episode_number": 999,
            "guest_name": "Test Guest",
            "transcript": " ".join([
                f"This is sentence {i} of the test transcript." 
                for i in range(50)
            ])
        }
        test_file.write_text(json.dumps(test_data))
        
        # Load and chunk
        loader = TranscriptLoader(str(tmp_path))
        transcript = loader.load_json(test_file)
        
        chunker = TranscriptChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_text(transcript.full_text)
        
        # Verify results
        assert transcript.title == "Integration Test Episode"
        assert len(chunks) > 1  # Should create multiple chunks
        assert all(c.chunk_index == i for i, c in enumerate(chunks))
        assert all(c.token_count > 0 for c in chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
