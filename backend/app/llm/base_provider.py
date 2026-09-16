"""
Base class for LLM providers with unified interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass


@dataclass
class Message:
    """A message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class CompletionResponse:
    """Response from LLM completion."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None  # token counts
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Provides a unified interface for different LLM backends
    (Anthropic, OpenAI, Ollama, etc.).
    """
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        """
        Initialize the LLM provider.
        
        Args:
            model: Model identifier
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Generate a completion given a list of messages.
        
        Args:
            messages: List of conversation messages
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Provider-specific parameters
        
        Returns:
            Completion response
        """
        pass
    
    @abstractmethod
    def stream_complete(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream a completion given a list of messages.
        
        Args:
            messages: List of conversation messages
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Provider-specific parameters
        
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the provider is available and working.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def format_messages(self, messages: List[Message]) -> Any:
        """
        Format messages for the specific provider's API.
        
        Args:
            messages: List of messages
        
        Returns:
            Provider-specific message format
        """
        # Default implementation returns as-is
        return messages
