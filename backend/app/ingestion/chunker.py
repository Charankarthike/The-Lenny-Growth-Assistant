"""
Text chunking utilities for transcript segmentation.
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

import tiktoken

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """A chunk of text with metadata."""
    content: str
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    metadata: dict


class TranscriptChunker:
    """
    Chunks transcripts into overlapping segments for embedding and retrieval.
    
    Strategy:
    - Respects sentence boundaries when possible
    - Maintains context with overlap between chunks
    - Preserves speaker attribution and timestamps if present
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"  # GPT-4, GPT-3.5, text-embedding-ada-002
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target size in tokens (default from settings)
            chunk_overlap: Overlap size in tokens (default from settings)
            encoding_name: Tiktoken encoding name
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Load tokenizer
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning("failed_to_load_tiktoken_encoding", error=str(e))
            # Fallback to approximate token counting
            self.encoding = None
        
        logger.info(
            "chunker_initialized",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in text.
        
        Args:
            text: Text to count tokens in
        
        Returns:
            Token count
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Approximate: ~4 characters per token
            return len(text) // 4
    
    def chunk_text(
        self,
        text: str,
        preserve_speakers: bool = True
    ) -> List[TextChunk]:
        """
        Chunk text into overlapping segments.
        
        Args:
            text: Full text to chunk
            preserve_speakers: Try to preserve speaker boundaries
        
        Returns:
            List of TextChunk objects
        """
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_tokens = 0
        current_char_start = 0
        current_char_pos = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence would exceed chunk_size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create a chunk
                chunk_text = ' '.join(current_chunk)
                chunk_end = current_char_pos
                
                chunks.append(TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    start_char=current_char_start,
                    end_char=chunk_end,
                    metadata=self._extract_metadata(chunk_text)
                ))
                
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_sentences, overlap_tokens = self._get_overlap_sentences(
                    current_chunk,
                    self.chunk_overlap
                )
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
                current_char_start = chunk_end - len(' '.join(overlap_sentences))
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
            current_char_pos += len(sentence) + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_text,
                chunk_index=chunk_index,
                token_count=current_tokens,
                start_char=current_char_start,
                end_char=len(text),
                metadata=self._extract_metadata(chunk_text)
            ))
        
        logger.info(
            "text_chunked",
            num_chunks=len(chunks),
            avg_tokens=sum(c.token_count for c in chunks) / len(chunks) if chunks else 0
        )
        
        return chunks
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better chunking.
        
        Args:
            text: Raw text
        
        Returns:
            Preprocessed text
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, respecting common abbreviations.
        
        Args:
            text: Text to split
        
        Returns:
            List of sentences
        """
        # Common abbreviations that don't end sentences
        abbreviations = r'(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|Inc|Ltd|Co)'
        
        # Split on period, question mark, or exclamation followed by space and capital
        # But not if preceded by common abbreviations
        pattern = rf'(?<!{abbreviations})(?<=[.!?])\s+(?=[A-Z])'
        
        sentences = re.split(pattern, text)
        
        # Filter out very short sentences (likely errors)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return sentences
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        overlap_tokens: int
    ) -> Tuple[List[str], int]:
        """
        Get the last N sentences that fit within overlap_tokens.
        
        Args:
            sentences: List of sentences
            overlap_tokens: Target overlap size in tokens
        
        Returns:
            Tuple of (overlap sentences, actual token count)
        """
        overlap = []
        tokens = 0
        
        # Work backwards from the end
        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if tokens + sentence_tokens > overlap_tokens:
                break
            overlap.insert(0, sentence)
            tokens += sentence_tokens
        
        return overlap, tokens
    
    def _extract_metadata(self, chunk_text: str) -> dict:
        """
        Extract metadata from chunk text (speaker, timestamps, etc.).
        
        Args:
            chunk_text: Chunk text to analyze
        
        Returns:
            Metadata dictionary
        """
        metadata = {}
        
        # Detect speaker patterns (e.g., "John: ", "SPEAKER 1: ")
        speaker_match = re.search(r'^([A-Z][A-Za-z\s]+):\s', chunk_text)
        if speaker_match:
            metadata['speaker'] = speaker_match.group(1).strip()
        
        # Detect timestamps (e.g., "[00:12:34]", "(12:34)")
        timestamp_match = re.search(r'[\[\(]?(\d{1,2}:\d{2}(?::\d{2})?)[\]\)]?', chunk_text)
        if timestamp_match:
            metadata['timestamp'] = timestamp_match.group(1)
        
        return metadata
    
    def get_chunk_with_context(
        self,
        chunks: List[TextChunk],
        chunk_index: int,
        context_size: int = 1
    ) -> str:
        """
        Get a chunk with surrounding context for better retrieval.
        
        Args:
            chunks: List of all chunks
            chunk_index: Index of target chunk
            context_size: Number of chunks before/after to include
        
        Returns:
            Chunk text with context
        """
        if not chunks or chunk_index < 0 or chunk_index >= len(chunks):
            return ""
        
        start_idx = max(0, chunk_index - context_size)
        end_idx = min(len(chunks), chunk_index + context_size + 1)
        
        context_chunks = chunks[start_idx:end_idx]
        return ' [...] '.join(c.content for c in context_chunks)
